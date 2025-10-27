"""Application services - business logic orchestration."""
from typing import List, Optional
from datetime import datetime
import uuid

from domain.entities import Pair
from domain.interfaces import IPairRepository, ISearchEngine
from application.dto import PairCreateDTO, PairUpdateDTO, PairResponseDTO, DeleteResponseDTO


class PairService:
    """Service for managing pairs - orchestrates business logic."""

    def __init__(self, repository: IPairRepository, search_engine: ISearchEngine):
        """Initialize service with repository and search engine dependencies."""
        self.repository = repository
        self.search_engine = search_engine

    async def get_all_pairs(self) -> List[PairResponseDTO]:
        """Retrieve all pairs."""
        pairs = await self.repository.get_all()
        return [self._to_dto(pair) for pair in pairs]

    async def get_pair_by_id(self, pair_id: str) -> Optional[PairResponseDTO]:
        """Retrieve a specific pair by ID."""
        pair = await self.repository.get_by_id(pair_id)
        return self._to_dto(pair) if pair else None

    async def create_pair(self, dto: PairCreateDTO) -> PairResponseDTO:
        """Create a new pair."""
        pair = Pair(
            id=str(uuid.uuid4()),
            field1=dto.field1,
            field2=dto.field2,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )

        created_pair = await self.repository.create(pair)

        # Index for search
        await self.search_engine.index_pair(created_pair)

        return self._to_dto(created_pair)

    async def update_pair(self, pair_id: str, dto: PairUpdateDTO) -> Optional[PairResponseDTO]:
        """Update an existing pair."""
        existing_pair = await self.repository.get_by_id(pair_id)
        if not existing_pair:
            return None

        # Update only provided fields
        if dto.field1 is not None:
            existing_pair.field1 = dto.field1
        if dto.field2 is not None:
            existing_pair.field2 = dto.field2
        existing_pair.updated_at = datetime.utcnow()

        updated_pair = await self.repository.update(existing_pair)

        if updated_pair:
            # Re-index for search
            await self.search_engine.index_pair(updated_pair)

        return self._to_dto(updated_pair) if updated_pair else None

    async def delete_pair(self, pair_id: str) -> bool:
        """Delete a pair by ID."""
        result = await self.repository.delete(pair_id)

        if result:
            await self.search_engine.delete_pair_index(pair_id)

        return result

    async def delete_all_pairs(self) -> DeleteResponseDTO:
        """Delete all pairs."""
        deleted_count = await self.repository.delete_all()

        # Clear search indices
        await self.search_engine.delete_all_indices()

        return DeleteResponseDTO(
            deleted_count=deleted_count,
            message=f"Successfully deleted {deleted_count} pairs"
        )

    async def search_pairs(self, query: str) -> List[PairResponseDTO]:
        """Search pairs using search engine."""
        pair_ids = await self.search_engine.search_pairs(query)

        pairs = []
        for pair_id in pair_ids:
            pair = await self.repository.get_by_id(pair_id)
            if pair:
                pairs.append(pair)

        return [self._to_dto(pair) for pair in pairs]

    @staticmethod
    def _to_dto(pair: Pair) -> PairResponseDTO:
        """Convert domain entity to DTO."""
        return PairResponseDTO(
            id=pair.id,
            field1=pair.field1,
            field2=pair.field2,
            created_at=pair.created_at,
            updated_at=pair.updated_at
        )
