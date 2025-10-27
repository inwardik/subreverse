"""Elasticsearch search engine implementation."""
from typing import List, Optional
from elasticsearch import AsyncElasticsearch
from domain.entities import SubtitlePair
from domain.interfaces import ISearchEngine


class ElasticsearchEngine(ISearchEngine):
    """Elasticsearch implementation for search functionality."""

    def __init__(self, es_url: str, index_name: str):
        self.es_url = es_url
        self.index_name = index_name
        self._client: Optional[AsyncElasticsearch] = None

    async def _get_client(self) -> AsyncElasticsearch:
        """Get or create Elasticsearch client."""
        if self._client is None:
            self._client = AsyncElasticsearch([self.es_url], verify_certs=False)
        return self._client

    async def close(self):
        """Close Elasticsearch client."""
        if self._client:
            await self._client.close()
            self._client = None

    async def _ensure_index(self) -> None:
        """Ensure index exists with proper mappings."""
        client = await self._get_client()

        if await client.indices.exists(index=self.index_name):
            return

        # Create index with mappings
        mappings = {
            "mappings": {
                "properties": {
                    "en": {
                        "type": "text",
                        "analyzer": "standard"
                    },
                    "ru": {
                        "type": "text",
                        "analyzer": "standard"
                    },
                    "rating": {
                        "type": "integer"
                    },
                    "file_en": {"type": "keyword"},
                    "file_ru": {"type": "keyword"},
                    "time_en": {"type": "keyword"},
                    "time_ru": {"type": "keyword"},
                    "category": {"type": "keyword"},
                    "seq_id": {"type": "integer"}
                }
            },
            "settings": {
                "number_of_shards": 1,
                "number_of_replicas": 0
            }
        }

        await client.indices.create(index=self.index_name, body=mappings)

    async def index_pair(self, pair: SubtitlePair) -> None:
        """Index a single pair."""
        client = await self._get_client()
        await self._ensure_index()

        doc = {
            "en": pair.en,
            "ru": pair.ru,
            "rating": pair.rating,
            "file_en": pair.file_en,
            "file_ru": pair.file_ru,
            "time_en": pair.time_en,
            "time_ru": pair.time_ru,
            "category": pair.category,
            "seq_id": pair.seq_id
        }

        await client.index(index=self.index_name, id=pair.id, document=doc)

    async def index_many(self, pairs: List[SubtitlePair]) -> int:
        """Index many pairs using bulk API. Returns count indexed."""
        if not pairs:
            return 0

        client = await self._get_client()
        await self._ensure_index()

        # Build bulk operations
        operations = []
        for pair in pairs:
            operations.append({"index": {"_index": self.index_name, "_id": pair.id}})
            operations.append({
                "en": pair.en,
                "ru": pair.ru,
                "rating": pair.rating,
                "file_en": pair.file_en,
                "file_ru": pair.file_ru,
                "time_en": pair.time_en,
                "time_ru": pair.time_ru,
                "category": pair.category,
                "seq_id": pair.seq_id
            })

        try:
            response = await client.bulk(operations=operations)
            # Count successful operations
            indexed = 0
            if response.get("items"):
                for item in response["items"]:
                    if "index" in item and item["index"].get("status") in [200, 201]:
                        indexed += 1
            return indexed
        except Exception:
            return 0

    async def search_pairs(self, query: str, limit: int = 100) -> List[str]:
        """Search pairs and return list of IDs."""
        client = await self._get_client()

        # Check if index exists
        if not await client.indices.exists(index=self.index_name):
            return []

        # Build search query with rating boost
        body = {
            "query": {
                "function_score": {
                    "query": {
                        "multi_match": {
                            "query": query,
                            "fields": ["en^2", "ru"],
                            "operator": "and"
                        }
                    },
                    "boost_mode": "sum",
                    "score_mode": "sum",
                    "functions": [
                        {
                            "field_value_factor": {
                                "field": "rating",
                                "factor": 0.2,
                                "modifier": "none",
                                "missing": 0
                            }
                        }
                    ]
                }
            },
            "size": limit
        }

        try:
            response = await client.search(index=self.index_name, body=body)
            hits = response.get("hits", {}).get("hits", [])
            return [hit["_id"] for hit in hits]
        except Exception:
            return []

    async def delete_pair_index(self, pair_id: str) -> None:
        """Remove pair from search index."""
        client = await self._get_client()
        try:
            await client.delete(index=self.index_name, id=pair_id, ignore=[404])
        except Exception:
            pass

    async def delete_all_indices(self) -> None:
        """Clear all search indices."""
        client = await self._get_client()
        try:
            await client.indices.delete(index=self.index_name, ignore=[404])
        except Exception:
            pass

    async def reindex_all(self, pairs: List[SubtitlePair]) -> int:
        """Reindex all pairs. Returns count indexed."""
        client = await self._get_client()

        # Delete existing index
        try:
            await client.indices.delete(index=self.index_name, ignore=[404])
        except Exception:
            pass

        # Recreate index
        await self._ensure_index()

        # Index in batches
        BATCH_SIZE = 1000
        total_indexed = 0

        for i in range(0, len(pairs), BATCH_SIZE):
            batch = pairs[i:i + BATCH_SIZE]
            indexed = await self.index_many(batch)
            total_indexed += indexed

        return total_indexed
