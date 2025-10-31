"""Authentication service - handles user registration, login, and token verification."""
from typing import Optional
from datetime import datetime, timedelta
import uuid

from domain.entities import User
from domain.interfaces import IUserRepository, IPasswordHandler, IJWTHandler
from application.dto import SignupDTO, LoginDTO, TokenResponseDTO, UserResponseDTO, SelfResponseDTO


class AuthService:
    """Service for authentication and user management."""

    def __init__(
        self,
        user_repository: IUserRepository,
        password_handler: IPasswordHandler,
        jwt_handler: IJWTHandler,
        jwt_expire_seconds: int = 604800  # 7 days default
    ):
        """Initialize service with dependencies."""
        self.user_repository = user_repository
        self.password_handler = password_handler
        self.jwt_handler = jwt_handler
        self.jwt_expire_seconds = jwt_expire_seconds

    async def signup(self, dto: SignupDTO) -> TokenResponseDTO:
        """Register a new user and return token."""
        # Check if user already exists
        existing_email = await self.user_repository.get_by_email(dto.email.lower())
        if existing_email:
            raise ValueError("Email already registered")

        existing_username = await self.user_repository.get_by_username(dto.username)
        if existing_username:
            raise ValueError("Username already taken")

        # Hash password
        password_hash, salt = self.password_handler.hash_password(dto.password)

        # Create user entity
        now = datetime.utcnow()
        user = User(
            id=str(uuid.uuid4()),
            username=dto.username,
            email=dto.email.lower(),
            password_hash=password_hash,
            salt=salt,
            created_at=now,
            energy=10,
            max_energy=10,
            level=1,
            xp=0,
            role="user",
            last_recharge=now
        )

        # Save to database
        created_user = await self.user_repository.create(user)

        # Generate token
        token = self._generate_token(created_user)

        # Return response
        return TokenResponseDTO(
            token=token,
            user=self._to_user_dto(created_user)
        )

    async def login(self, dto: LoginDTO) -> TokenResponseDTO:
        """Authenticate user and return token."""
        # Try to find user by email or username
        user = await self.user_repository.get_by_email(dto.login.lower())
        if not user:
            user = await self.user_repository.get_by_username(dto.login)

        if not user:
            raise ValueError("Invalid credentials")

        # Verify password
        if not self.password_handler.verify_password(
            dto.password,
            user.password_hash,
            user.salt
        ):
            raise ValueError("Invalid credentials")

        # Generate token
        token = self._generate_token(user)

        # Return response
        return TokenResponseDTO(
            token=token,
            user=self._to_user_dto(user)
        )

    async def verify_token(self, token: str) -> Optional[User]:
        """Verify JWT token and return user."""
        try:
            payload = self.jwt_handler.decode(token)
        except Exception:
            return None

        # Load user from database
        user_id = payload.get("sub")
        if not user_id:
            return None

        user = await self.user_repository.get_by_id(user_id)
        return user

    async def get_user_by_id(self, user_id: str) -> Optional[UserResponseDTO]:
        """Get user by ID."""
        user = await self.user_repository.get_by_id(user_id)
        return self._to_user_dto(user) if user else None

    async def get_self(self, user_id: str) -> Optional[SelfResponseDTO]:
        """Get user info with energy recharge logic for /self endpoint."""
        user = await self.user_repository.get_by_id(user_id)
        if not user:
            return None

        # Check if new day started and recharge energy
        await self.user_repository.recharge_energy(user_id)

        # Reload user to get updated energy
        user = await self.user_repository.get_by_id(user_id)
        if not user:
            return None

        # Calculate max_xp
        max_xp = user.level * 10

        return SelfResponseDTO(
            id=user.id,
            username=user.username,
            email=user.email,
            energy=user.energy,
            max_energy=user.max_energy,
            level=user.level,
            xp=user.xp,
            max_xp=max_xp,
            role=user.role
        )

    def _generate_token(self, user: User) -> str:
        """Generate JWT token for user."""
        now = datetime.utcnow()
        payload = {
            "sub": user.id,
            "username": user.username,
            "email": user.email,
            "iat": int(now.timestamp()),
            "exp": int((now + timedelta(seconds=self.jwt_expire_seconds)).timestamp())
        }
        return self.jwt_handler.encode(payload)

    @staticmethod
    def _to_user_dto(user: User) -> UserResponseDTO:
        """Convert User entity to UserResponseDTO."""
        return UserResponseDTO(
            id=user.id,
            username=user.username,
            email=user.email,
            energy=user.energy,
            max_energy=user.max_energy,
            level=user.level,
            xp=user.xp,
            role=user.role,
            created_at=user.created_at
        )
