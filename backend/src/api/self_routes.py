"""Self endpoint - separate from auth for clarity."""
from fastapi import APIRouter, Depends, HTTPException, status

from application.auth_service import AuthService
from application.dto import SelfResponseDTO
from api.dependencies import get_auth_service, get_current_user
from domain.entities import User


router = APIRouter(tags=["user"])


@router.get("/self", response_model=SelfResponseDTO)
async def get_self(
    current_user: User = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Get current user information with energy recharge logic.

    This endpoint:
    - Returns user info including energy, level, xp
    - Automatically recharges energy to max if a new day has started
    - Calculates max_xp based on level

    Requires:
        Valid JWT token in Authorization header

    Returns:
        Current user information with energy and leveling data

    Raises:
        401: Not authenticated
    """
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )

    result = await auth_service.get_self(current_user.id)

    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    return result
