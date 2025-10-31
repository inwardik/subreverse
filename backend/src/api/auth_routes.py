"""Authentication routes."""
from fastapi import APIRouter, Depends, HTTPException, status

from application.auth_service import AuthService
from application.dto import (
    SignupDTO,
    LoginDTO,
    TokenResponseDTO,
    UserResponseDTO,
    SelfResponseDTO
)
from api.dependencies import get_auth_service, get_current_user
from domain.entities import User


router = APIRouter(prefix="/auth", tags=["authentication"])


@router.post("/signup", response_model=TokenResponseDTO, status_code=status.HTTP_201_CREATED)
async def signup(
    data: SignupDTO,
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Register a new user.

    Args:
        data: User registration data (username, email, password)

    Returns:
        JWT token and user information

    Raises:
        409: Email or username already exists
        400: Invalid data
    """
    try:
        return await auth_service.signup(data)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create user: {str(e)}"
        )


@router.post("/login", response_model=TokenResponseDTO)
async def login(
    data: LoginDTO,
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Authenticate user and return token.

    Args:
        data: Login credentials (email/username and password)

    Returns:
        JWT token and user information

    Raises:
        401: Invalid credentials
    """
    try:
        return await auth_service.login(data)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Login failed: {str(e)}"
        )


@router.get("/me", response_model=UserResponseDTO)
async def get_me(
    current_user: User = Depends(get_current_user)
):
    """
    Get current authenticated user information.

    Requires:
        Valid JWT token in Authorization header

    Returns:
        Current user information

    Raises:
        401: Not authenticated
    """
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )

    from application.auth_service import AuthService
    # Convert User entity to DTO
    return AuthService._to_user_dto(current_user)
