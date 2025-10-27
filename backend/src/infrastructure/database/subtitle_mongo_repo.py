"""MongoDB repository implementation for subtitle pairs, idioms, quotes, and stats."""
from typing import List, Optional
import random
import re
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId
from datetime import datetime

from domain.entities import SubtitlePair, Idiom, Quote, SystemStats
from domain.interfaces import (
    ISubtitlePairRepository,
    IIdiomRepository,
    IQuoteRepository,
    IStatsRepository
)


class MongoDBSubtitlePairRepository(ISubtitlePairRepository):
    """MongoDB implementation for SubtitlePair repository."""

    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.collection = db["pairs"]
        self._ensure_indexes()

    def _ensure_indexes(self):
        """Ensure indexes are created."""
        import asyncio
        async def create_indexes():
            try:
                await self.collection.create_index([("seq_id", 1)], name="seq_id_idx", unique=True, sparse=True)
                await self.collection.create_index([("en", 1)], name="en_index")
                await self.collection.create_index([("ru", 1)], name="ru_index")
            except Exception:
                pass
        asyncio.create_task(create_indexes())

    async def get_all(self) -> List[SubtitlePair]:
        cursor = self.collection.find()
        documents = await cursor.to_list(length=None)
        return [self._doc_to_entity(doc) for doc in documents]

    async def get_by_id(self, pair_id: str) -> Optional[SubtitlePair]:
        try:
            oid = ObjectId(pair_id)
        except Exception:
            return None
        document = await self.collection.find_one({"_id": oid})
        return self._doc_to_entity(document) if document else None

    async def get_by_seq_id(self, seq_id: int) -> Optional[SubtitlePair]:
        document = await self.collection.find_one({"seq_id": seq_id})
        return self._doc_to_entity(document) if document else None

    async def get_random(self) -> Optional[SubtitlePair]:
        """Get a random pair using seq_id if available, fallback to skip."""
        try:
            total = await self.collection.estimated_document_count()
            if not total:
                return None

            # Try seq_id approach first
            lo, hi = 1, total
            for _ in range(5):
                rnd = random.randint(lo, hi)
                doc = await self.collection.find_one({"seq_id": rnd})
                if doc:
                    return self._doc_to_entity(doc)

            # Fallback to skip
            random_skip = random.randint(0, max(0, total - 1))
            cursor = self.collection.find().skip(random_skip).limit(1)
            docs = await cursor.to_list(length=1)
            if docs:
                return self._doc_to_entity(docs[0])

            # Final fallback to $sample
            cursor = self.collection.aggregate([{"$sample": {"size": 1}}])
            docs = await cursor.to_list(length=1)
            return self._doc_to_entity(docs[0]) if docs else None
        except Exception:
            return None

    async def get_neighbor(self, pair_id: str, offset: int) -> Optional[SubtitlePair]:
        """Get neighbor pair by temporal offset within same file."""
        base = await self.get_by_id(pair_id)
        if not base:
            return None

        if offset == 0:
            return base

        # Fast path using seq_id
        if base.seq_id is not None and abs(offset) <= 100:
            target_seq = base.seq_id + offset
            neighbor = await self.get_by_seq_id(target_seq)
            if neighbor:
                return neighbor

        # Slow path: temporal navigation within same file
        group_file = base.file_en or base.file_ru
        if not group_file:
            return base

        time_field = "time_en" if base.time_en else "time_ru"
        base_start = self._parse_start_ms(getattr(base, time_field, None))
        if base_start < 0:
            return base

        # Fetch all docs from same file
        cursor = self.collection.find(
            {"$or": [{"file_en": group_file}, {"file_ru": group_file}]},
            projection={"en": 1, "ru": 1, "file_en": 1, "file_ru": 1, "time_en": 1, "time_ru": 1}
        )
        docs = await cursor.to_list(length=None)

        # Sort by time
        enriched = []
        for d in docs:
            ts = d.get(time_field)
            start = self._parse_start_ms(ts)
            if start < 0 and time_field:
                other = "time_ru" if time_field == "time_en" else "time_en"
                start = self._parse_start_ms(d.get(other))
            if start >= 0:
                enriched.append((start, d))

        enriched.sort(key=lambda x: x[0])

        # Find base position
        base_oid = ObjectId(pair_id)
        pos = None
        for i, (_, d) in enumerate(enriched):
            if d.get("_id") == base_oid:
                pos = i
                break

        if pos is None:
            return base

        target_index = pos + offset
        if target_index < 0 or target_index >= len(enriched):
            return base

        _, target_doc = enriched[target_index]
        return self._doc_to_entity(target_doc)

    def _parse_start_ms(self, time_str: Optional[str]) -> int:
        """Parse SRT time string to milliseconds."""
        if not time_str:
            return -1
        m = re.match(r"^(\d{2}):(\d{2}):(\d{2}),(\d{3})\s*-->", time_str)
        if not m:
            return -1
        h, mi, s, ms = map(int, m.groups())
        return h * 3600000 + mi * 60000 + s * 1000 + ms

    async def create(self, pair: SubtitlePair) -> SubtitlePair:
        document = self._entity_to_doc(pair)
        result = await self.collection.insert_one(document)
        pair.id = str(result.inserted_id)
        return pair

    async def create_many(self, pairs: List[SubtitlePair]) -> int:
        if not pairs:
            return 0
        documents = [self._entity_to_doc(p) for p in pairs]
        result = await self.collection.insert_many(documents)
        return len(result.inserted_ids)

    async def update(self, pair: SubtitlePair) -> Optional[SubtitlePair]:
        try:
            oid = ObjectId(pair.id)
        except Exception:
            return None
        document = self._entity_to_doc(pair)
        result = await self.collection.replace_one({"_id": oid}, document)
        return pair if result.modified_count > 0 else None

    async def update_rating(self, pair_id: str, delta: int) -> Optional[SubtitlePair]:
        try:
            oid = ObjectId(pair_id)
        except Exception:
            return None
        from pymongo import ReturnDocument
        updated = await self.collection.find_one_and_update(
            {"_id": oid},
            {"$inc": {"rating": delta}},
            return_document=ReturnDocument.AFTER
        )
        return self._doc_to_entity(updated) if updated else None

    async def update_category(self, pair_id: str, category: Optional[str]) -> Optional[SubtitlePair]:
        try:
            oid = ObjectId(pair_id)
        except Exception:
            return None
        from pymongo import ReturnDocument
        if category is None or category == "":
            update_op = {"$unset": {"category": ""}}
        else:
            update_op = {"$set": {"category": category}}
        updated = await self.collection.find_one_and_update(
            {"_id": oid},
            update_op,
            return_document=ReturnDocument.AFTER
        )
        return self._doc_to_entity(updated) if updated else None

    async def delete(self, pair_id: str) -> bool:
        try:
            oid = ObjectId(pair_id)
        except Exception:
            return False
        result = await self.collection.delete_one({"_id": oid})
        return result.deleted_count > 0

    async def delete_all(self) -> int:
        result = await self.collection.delete_many({})
        return result.deleted_count

    async def clear_duplicates(self) -> int:
        """Remove duplicate pairs by (en, ru) keeping only one."""
        pipeline = [
            {"$project": {"en": {"$ifNull": ["$en", ""]}, "ru": {"$ifNull": ["$ru", ""]}}},
            {"$group": {"_id": {"en": "$en", "ru": "$ru"}, "count": {"$sum": 1}, "ids": {"$push": "$_id"}}},
            {"$match": {"count": {"$gt": 1}}}
        ]
        dup_groups = await self.collection.aggregate(pipeline, allowDiskUse=True).to_list(length=None)

        to_delete_ids = []
        for g in dup_groups:
            ids = g.get("ids", [])
            if isinstance(ids, list) and len(ids) > 1:
                to_delete_ids.extend(ids[1:])

        deleted_count = 0
        CHUNK = 1000
        for i in range(0, len(to_delete_ids), CHUNK):
            chunk = to_delete_ids[i:i+CHUNK]
            result = await self.collection.delete_many({"_id": {"$in": chunk}})
            deleted_count += result.deleted_count

        return deleted_count

    async def count_total(self) -> int:
        try:
            count = await self.collection.estimated_document_count()
            if count is None:
                count = await self.collection.count_documents({})
        except Exception:
            count = await self.collection.count_documents({})
        return count

    async def get_distinct_files_en(self) -> List[str]:
        files = await self.collection.distinct("file_en")
        files = [str(f).replace('_en.srt', '') for f in files if f]
        files.sort(key=lambda s: s.lower())
        return files

    @staticmethod
    def _entity_to_doc(pair: SubtitlePair) -> dict:
        doc = {
            "en": pair.en,
            "ru": pair.ru,
            "file_en": pair.file_en,
            "file_ru": pair.file_ru,
            "time_en": pair.time_en,
            "time_ru": pair.time_ru,
            "rating": pair.rating,
        }
        if pair.category is not None:
            doc["category"] = pair.category
        if pair.seq_id is not None:
            doc["seq_id"] = pair.seq_id
        if pair.id:
            try:
                doc["_id"] = ObjectId(pair.id)
            except Exception:
                pass
        return doc

    @staticmethod
    def _doc_to_entity(document: dict) -> SubtitlePair:
        return SubtitlePair(
            id=str(document["_id"]),
            en=document.get("en", ""),
            ru=document.get("ru", ""),
            file_en=document.get("file_en"),
            file_ru=document.get("file_ru"),
            time_en=document.get("time_en"),
            time_ru=document.get("time_ru"),
            rating=document.get("rating", 0),
            category=document.get("category"),
            seq_id=document.get("seq_id")
        )


class MongoDBIdiomRepository(IIdiomRepository):
    """MongoDB implementation for Idiom repository."""

    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.collection = db["idioms"]
        self._ensure_indexes()

    def _ensure_indexes(self):
        import asyncio
        async def create_indexes():
            try:
                await self.collection.create_index([("pair_seq_id", 1)], name="pair_seq_unique", unique=True, sparse=True)
                await self.collection.create_index([("owner_username", 1)], name="owner_idx", sparse=True)
                await self.collection.create_index([("rating", -1)], name="rating_idx", sparse=True)
            except Exception:
                pass
        asyncio.create_task(create_indexes())

    async def get_recent(self, limit: int = 10) -> List[Idiom]:
        cursor = self.collection.find().sort("_id", -1).limit(limit)
        docs = await cursor.to_list(length=limit)
        return [self._doc_to_entity(doc) for doc in docs]

    async def upsert(self, idiom: Idiom) -> Idiom:
        doc = self._entity_to_doc(idiom)
        filter_dict = {"pair_seq_id": idiom.pair_seq_id} if idiom.pair_seq_id is not None else {"_id": ObjectId()}
        await self.collection.update_one(filter_dict, {"$set": doc}, upsert=True)
        return idiom

    @staticmethod
    def _entity_to_doc(idiom: Idiom) -> dict:
        return {
            "en": idiom.en,
            "ru": idiom.ru,
            "pair_seq_id": idiom.pair_seq_id,
            "rating": idiom.rating,
            "filename": idiom.filename,
            "time": idiom.time,
            "owner_username": idiom.owner_username,
        }

    @staticmethod
    def _doc_to_entity(document: dict) -> Idiom:
        return Idiom(
            id=str(document["_id"]),
            en=document.get("en", ""),
            ru=document.get("ru", ""),
            pair_seq_id=document.get("pair_seq_id"),
            rating=document.get("rating", 0),
            filename=document.get("filename"),
            time=document.get("time"),
            owner_username=document.get("owner_username")
        )


class MongoDBQuoteRepository(IQuoteRepository):
    """MongoDB implementation for Quote repository."""

    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.collection = db["quotes"]
        self._ensure_indexes()

    def _ensure_indexes(self):
        import asyncio
        async def create_indexes():
            try:
                await self.collection.create_index([("pair_seq_id", 1)], name="pair_seq_unique", unique=True, sparse=True)
                await self.collection.create_index([("owner_username", 1)], name="owner_idx", sparse=True)
                await self.collection.create_index([("rating", -1)], name="rating_idx", sparse=True)
            except Exception:
                pass
        asyncio.create_task(create_indexes())

    async def get_recent(self, limit: int = 10) -> List[Quote]:
        cursor = self.collection.find().sort("_id", -1).limit(limit)
        docs = await cursor.to_list(length=limit)
        return [self._doc_to_entity(doc) for doc in docs]

    async def upsert(self, quote: Quote) -> Quote:
        doc = self._entity_to_doc(quote)
        filter_dict = {"pair_seq_id": quote.pair_seq_id} if quote.pair_seq_id is not None else {"_id": ObjectId()}
        await self.collection.update_one(filter_dict, {"$set": doc}, upsert=True)
        return quote

    @staticmethod
    def _entity_to_doc(quote: Quote) -> dict:
        return {
            "en": quote.en,
            "ru": quote.ru,
            "pair_seq_id": quote.pair_seq_id,
            "rating": quote.rating,
            "filename": quote.filename,
            "time": quote.time,
            "owner_username": quote.owner_username,
        }

    @staticmethod
    def _doc_to_entity(document: dict) -> Quote:
        return Quote(
            id=str(document["_id"]),
            en=document.get("en", ""),
            ru=document.get("ru", ""),
            pair_seq_id=document.get("pair_seq_id"),
            rating=document.get("rating", 0),
            filename=document.get("filename"),
            time=document.get("time"),
            owner_username=document.get("owner_username")
        )


class MongoDBStatsRepository(IStatsRepository):
    """MongoDB implementation for SystemStats repository."""

    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.collection = db["system_stats"]

    async def get_latest(self) -> Optional[SystemStats]:
        doc = await self.collection.find_one({"_id": "latest"})
        return self._doc_to_entity(doc) if doc else None

    async def save(self, stats: SystemStats) -> SystemStats:
        doc = {
            "_id": "latest",
            "total": stats.total,
            "files_en": stats.files_en,
            "updated_at": datetime.utcnow().isoformat() + "Z"
        }
        await self.collection.replace_one({"_id": "latest"}, doc, upsert=True)
        return stats

    @staticmethod
    def _doc_to_entity(document: dict) -> SystemStats:
        return SystemStats(
            total=document.get("total", 0),
            files_en=document.get("files_en", []),
            updated_at=document.get("updated_at")
        )
