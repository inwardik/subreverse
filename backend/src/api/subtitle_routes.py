"""API routes for subtitle pairs, idioms, quotes, and stats."""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional

from application.subtitle_service import SubtitlePairService
from application.dto import (
    SubtitlePairResponseDTO,
    SubtitlePairUpdateDTO,
    IdiomResponseDTO,
    QuoteResponseDTO,
    StatsResponseDTO,
    DeleteResponseDTO,
    ClearDuplicatesResponseDTO
)
from api.dependencies import get_subtitle_service, get_current_user, get_admin_user
from domain.entities import User


router = APIRouter(prefix="/api", tags=["subtitles"])


@router.get("/get_random", response_model=SubtitlePairResponseDTO)
async def get_random_pair(
    service: SubtitlePairService = Depends(get_subtitle_service)
):
    """Get a random subtitle pair."""
    pair = await service.get_random_pair()
    if not pair:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No pairs found"
        )
    return pair


@router.get("/search/{id}/", response_model=SubtitlePairResponseDTO)
async def get_pair_by_id(
    id: str,
    offset: int = Query(0, description="Temporal offset for navigation"),
    service: SubtitlePairService = Depends(get_subtitle_service)
):
    """
    Get a subtitle pair by ID with optional offset for temporal navigation.
    - offset=0: returns the pair itself
    - offset>0: returns pair N steps forward in time (same file)
    - offset<0: returns pair N steps backward in time (same file)
    """
    pair = await service.get_pair_by_id(id, offset)
    if not pair:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pair not found"
        )
    return pair


@router.patch("/search/{id}/", response_model=SubtitlePairResponseDTO)
async def update_pair(
    id: str,
    delta: Optional[int] = Query(None, description="Rating delta (+1 or -1)"),
    category: Optional[str] = Query(None, description="Category: idiom, quote, wrong, or null to unset"),
    user: User = Depends(get_current_user),
    service: SubtitlePairService = Depends(get_subtitle_service)
):
    """
    Update a subtitle pair (rating or category).
    Requires authentication and consumes 1 energy per action.
    Exactly one of delta or category must be provided.
    """
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )

    update_data = SubtitlePairUpdateDTO(delta=delta, category=category)

    try:
        pair = await service.update_pair(id, update_data, user)
        if not pair:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Pair not found"
            )
        return pair
    except ValueError as e:
        if "energy" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=str(e)
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/delete_all", response_model=DeleteResponseDTO)
async def delete_all_pairs(
    service: SubtitlePairService = Depends(get_subtitle_service),
    admin_user: User = Depends(get_admin_user)
):
    """
    Delete all subtitle pairs from the system.
    Requires admin role.
    """
    return await service.delete_all_pairs()


@router.post("/clear", response_model=ClearDuplicatesResponseDTO)
async def clear_duplicates(
    service: SubtitlePairService = Depends(get_subtitle_service),
    admin_user: User = Depends(get_admin_user)
):
    """
    Find and delete duplicate documents having the same (en, ru) pair.
    Keeps exactly one document per distinct (en, ru) value combination.
    Requires admin role.
    """
    return await service.clear_duplicates()


@router.get("/stats", response_model=StatsResponseDTO)
async def get_stats(
    service: SubtitlePairService = Depends(get_subtitle_service)
):
    """
    Return latest precomputed statistics.
    If no stats are present, return defaults.
    """
    return await service.get_stats()


@router.post("/stats", response_model=StatsResponseDTO)
async def compute_stats(
    service: SubtitlePairService = Depends(get_subtitle_service),
    admin_user: User = Depends(get_admin_user)
):
    """
    Compute statistics (total and files_en) and store them.
    Requires admin role.
    """
    return await service.compute_stats()


@router.get("/idioms", response_model=List[IdiomResponseDTO])
async def list_idioms(
    limit: int = Query(100, description="Maximum number of idioms to return"),
    status: Optional[str] = Query(None, description="Filter by status: draft, active, or deleted"),
    service: SubtitlePairService = Depends(get_subtitle_service)
):
    """Return idioms sorted by creation time descending, with optional status filter."""
    return await service.get_recent_idioms(limit, status)


@router.get("/quotes", response_model=List[QuoteResponseDTO])
async def list_quotes(
    service: SubtitlePairService = Depends(get_subtitle_service)
):
    """Return the 10 most recent quotes sorted by insertion time descending."""
    return await service.get_recent_quotes(10)


@router.get("/search", response_model=List[SubtitlePairResponseDTO])
async def search_pairs(
    q: str = Query(..., min_length=1, description="Text to search across 'en' and 'ru' fields"),
    service: SubtitlePairService = Depends(get_subtitle_service)
):
    """
    Search for subtitle pairs matching the query.
    - Searches in both 'en' and 'ru' fields (case-insensitive)
    - Supports exact phrase search when query is enclosed in double quotes
    - Returns up to 100 matching results
    """
    return await service.search_pairs(q, limit=100)


@router.post("/index_elastic_search")
async def reindex_elasticsearch(
    service: SubtitlePairService = Depends(get_subtitle_service),
    admin_user: User = Depends(get_admin_user)
):
    """
    Reindex all MongoDB documents into Elasticsearch.
    Strategy: delete existing index if present, recreate with mappings, then bulk index all docs in batches.
    Returns summary with total docs, indexed count, and elapsed time.
    Requires admin role.
    """
    try:
        result = await service.reindex_elasticsearch()
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reindex: {e}"
        )
