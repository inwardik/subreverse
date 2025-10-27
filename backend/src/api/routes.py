"""API routes for pairs management."""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List

from application.services import PairService
from application.dto import PairCreateDTO, PairUpdateDTO, PairResponseDTO, DeleteResponseDTO
from api.dependencies import get_pair_service


router = APIRouter(prefix="/api", tags=["pairs"])


@router.get("/pairs", response_model=List[PairResponseDTO])
async def get_all_pairs(
    service: PairService = Depends(get_pair_service)
):
    """
    Retrieve all pairs.

    Returns:
        List of all pairs in the system.
    """
    return await service.get_all_pairs()


@router.get("/pairs/{pair_id}", response_model=PairResponseDTO)
async def get_pair(
    pair_id: str,
    service: PairService = Depends(get_pair_service)
):
    """
    Retrieve a specific pair by ID.

    Args:
        pair_id: The unique identifier of the pair.

    Returns:
        The requested pair.

    Raises:
        404: If pair not found.
    """
    pair = await service.get_pair_by_id(pair_id)
    if not pair:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Pair with id '{pair_id}' not found"
        )
    return pair


@router.post("/pairs", response_model=PairResponseDTO, status_code=status.HTTP_201_CREATED)
async def create_pair(
    pair_data: PairCreateDTO,
    service: PairService = Depends(get_pair_service)
):
    """
    Create a new pair.

    Args:
        pair_data: The data for creating a new pair.

    Returns:
        The created pair with generated ID.
    """
    return await service.create_pair(pair_data)


@router.put("/pairs/{pair_id}", response_model=PairResponseDTO)
async def update_pair(
    pair_id: str,
    pair_data: PairUpdateDTO,
    service: PairService = Depends(get_pair_service)
):
    """
    Update an existing pair.

    Args:
        pair_id: The unique identifier of the pair to update.
        pair_data: The updated data (only provided fields will be updated).

    Returns:
        The updated pair.

    Raises:
        404: If pair not found.
    """
    pair = await service.update_pair(pair_id, pair_data)
    if not pair:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Pair with id '{pair_id}' not found"
        )
    return pair


@router.delete("/pairs/{pair_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_pair(
    pair_id: str,
    service: PairService = Depends(get_pair_service)
):
    """
    Delete a specific pair by ID.

    Args:
        pair_id: The unique identifier of the pair to delete.

    Raises:
        404: If pair not found.
    """
    result = await service.delete_pair(pair_id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Pair with id '{pair_id}' not found"
        )


@router.delete("/delete_all", response_model=DeleteResponseDTO)
async def delete_all_pairs(
    service: PairService = Depends(get_pair_service)
):
    """
    Delete all pairs from the system.

    Returns:
        Information about the deletion operation.
    """
    return await service.delete_all_pairs()


@router.get("/pairs/search", response_model=List[PairResponseDTO])
async def search_pairs(
    q: str = Query(..., description="Search query string"),
    service: PairService = Depends(get_pair_service)
):
    """
    Search pairs using Elasticsearch.

    Args:
        q: The search query string.

    Returns:
        List of pairs matching the search query.
    """
    return await service.search_pairs(q)
