"""Application service for subtitle pair operations."""
from typing import List, Optional
from datetime import datetime

from domain.entities import SubtitlePair, Idiom, Quote, SystemStats, User
from domain.interfaces import (
    ISubtitlePairRepository,
    IIdiomRepository,
    IQuoteRepository,
    IStatsRepository,
    IUserRepository,
    ISearchEngine
)
from application.dto import (
    SubtitlePairResponseDTO,
    SubtitlePairUpdateDTO,
    IdiomResponseDTO,
    QuoteResponseDTO,
    StatsResponseDTO,
    DeleteResponseDTO,
    ClearDuplicatesResponseDTO
)


class SubtitlePairService:
    """Service layer for subtitle pair business logic."""

    def __init__(
        self,
        pair_repo: ISubtitlePairRepository,
        idiom_repo: IIdiomRepository,
        quote_repo: IQuoteRepository,
        stats_repo: IStatsRepository,
        user_repo: IUserRepository,
        search_engine: Optional[ISearchEngine] = None
    ):
        self.pair_repo = pair_repo
        self.idiom_repo = idiom_repo
        self.quote_repo = quote_repo
        self.stats_repo = stats_repo
        self.user_repo = user_repo
        self.search_engine = search_engine

    async def get_random_pair(self) -> Optional[SubtitlePairResponseDTO]:
        """Get a random subtitle pair."""
        pair = await self.pair_repo.get_random()
        return self._to_dto(pair) if pair else None

    async def get_pair_by_id(self, pair_id: str, offset: int = 0) -> Optional[SubtitlePairResponseDTO]:
        """Get pair by ID with optional temporal offset."""
        if offset == 0:
            pair = await self.pair_repo.get_by_id(pair_id)
        else:
            pair = await self.pair_repo.get_neighbor(pair_id, offset)
        return self._to_dto(pair) if pair else None

    async def update_pair(
        self,
        pair_id: str,
        update_data: SubtitlePairUpdateDTO,
        user: User
    ) -> Optional[SubtitlePairResponseDTO]:
        """Update pair rating or category with energy consumption."""
        # Validate input
        has_delta = update_data.delta is not None
        has_category = update_data.category is not None

        if has_delta and has_category:
            raise ValueError("Provide only one of: delta or category")
        if not has_delta and not has_category:
            raise ValueError("Either delta or category must be provided")

        # Check and consume energy
        if user.energy <= 0:
            raise ValueError("Not enough energy")

        # Consume energy
        success = await self.user_repo.update_energy(user.id, -1)
        if not success:
            raise ValueError("Failed to consume energy")

        try:
            # Perform update
            if has_delta:
                updated = await self.pair_repo.update_rating(pair_id, update_data.delta)
            else:
                # Normalize category
                cat = update_data.category
                if cat and cat.strip().lower() in {"null", "none", ""}:
                    cat = None
                elif cat and cat not in {"idiom", "quote", "wrong"}:
                    raise ValueError("category must be one of: idiom, quote, wrong, or null")
                updated = await self.pair_repo.update_category(pair_id, cat)

            if not updated:
                # Refund energy if pair not found
                await self.user_repo.update_energy(user.id, 1)
                return None

            # Handle idiom/quote mirroring
            if updated.category == "idiom":
                idiom = Idiom(
                    id="",  # Will be assigned by repo
                    en=updated.en,
                    ru=updated.ru,
                    pair_seq_id=updated.seq_id,
                    rating=updated.rating,
                    filename=updated.file_en.replace("_en.srt", "") if updated.file_en else None,
                    time=updated.time_en,
                    owner_username=user.username
                )
                await self.idiom_repo.upsert(idiom)

            if updated.category == "quote":
                quote = Quote(
                    id="",
                    en=updated.en,
                    ru=updated.ru,
                    pair_seq_id=updated.seq_id,
                    rating=updated.rating,
                    filename=updated.file_en.replace("_en.srt", "") if updated.file_en else None,
                    time=updated.time_en,
                    owner_username=user.username
                )
                await self.quote_repo.upsert(quote)

            # Handle XP and leveling
            await self._handle_xp_gain(user)

            return self._to_dto(updated)
        except Exception as e:
            # Refund energy on error
            await self.user_repo.update_energy(user.id, 1)
            raise

    async def _handle_xp_gain(self, user: User):
        """Handle XP gain and leveling after action."""
        new_xp = user.xp + 1
        threshold = max(1, user.level * 10)

        if new_xp >= threshold:
            # Level up
            user.level += 1
            user.max_energy += 5
            user.xp = 0
            await self.user_repo.update(user)
        else:
            user.xp = new_xp
            await self.user_repo.update(user)

    async def delete_all_pairs(self) -> DeleteResponseDTO:
        """Delete all pairs."""
        deleted = await self.pair_repo.delete_all()
        if self.search_engine:
            await self.search_engine.delete_all_indices()
        return DeleteResponseDTO(
            deleted_count=deleted,
            message=f"Deleted {deleted} pairs"
        )

    async def clear_duplicates(self) -> ClearDuplicatesResponseDTO:
        """Remove duplicate pairs."""
        deleted = await self.pair_repo.clear_duplicates()
        return ClearDuplicatesResponseDTO(
            duplicate_groups=deleted,
            documents_deleted=deleted,
            documents_kept_per_group=1
        )

    async def get_stats(self) -> StatsResponseDTO:
        """Get system statistics."""
        stats = await self.stats_repo.get_latest()
        if not stats:
            return StatsResponseDTO(total=0, files_en=[])
        return StatsResponseDTO(
            total=stats.total,
            files_en=stats.files_en,
            updated_at=stats.updated_at
        )

    async def compute_stats(self) -> StatsResponseDTO:
        """Compute and save statistics."""
        total = await self.pair_repo.count_total()
        files_en = await self.pair_repo.get_distinct_files_en()
        stats = SystemStats(
            total=total,
            files_en=files_en,
            updated_at=datetime.utcnow().isoformat() + "Z"
        )
        await self.stats_repo.save(stats)
        return StatsResponseDTO(
            total=stats.total,
            files_en=stats.files_en,
            updated_at=stats.updated_at
        )

    async def get_recent_idioms(self, limit: int = 10) -> List[IdiomResponseDTO]:
        """Get recent idioms."""
        idioms = await self.idiom_repo.get_recent(limit)
        return [self._idiom_to_dto(i) for i in idioms]

    async def get_recent_quotes(self, limit: int = 10) -> List[QuoteResponseDTO]:
        """Get recent quotes."""
        quotes = await self.quote_repo.get_recent(limit)
        return [self._quote_to_dto(q) for q in quotes]

    @staticmethod
    def _to_dto(pair: SubtitlePair) -> SubtitlePairResponseDTO:
        return SubtitlePairResponseDTO(
            _id=pair.id,
            en=pair.en,
            ru=pair.ru,
            file_en=pair.file_en,
            file_ru=pair.file_ru,
            time_en=pair.time_en,
            time_ru=pair.time_ru,
            rating=pair.rating,
            category=pair.category,
            seq_id=pair.seq_id
        )

    @staticmethod
    def _idiom_to_dto(idiom: Idiom) -> IdiomResponseDTO:
        return IdiomResponseDTO(
            _id=idiom.id,
            en=idiom.en,
            ru=idiom.ru,
            filename=idiom.filename,
            time=idiom.time,
            owner_username=idiom.owner_username,
            rating=idiom.rating
        )

    @staticmethod
    def _quote_to_dto(quote: Quote) -> QuoteResponseDTO:
        return QuoteResponseDTO(
            _id=quote.id,
            en=quote.en,
            ru=quote.ru,
            filename=quote.filename,
            time=quote.time,
            owner_username=quote.owner_username,
            rating=quote.rating
        )
