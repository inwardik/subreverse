"""Repository interfaces - abstractions for data access."""
from abc import ABC, abstractmethod
from typing import List, Optional
from .entities import Pair, User


class IPairRepository(ABC):
    """Abstract repository interface for Pair entities."""

    @abstractmethod
    async def get_all(self) -> List[Pair]:
        """Retrieve all pairs from storage."""
        pass

    @abstractmethod
    async def get_by_id(self, pair_id: str) -> Optional[Pair]:
        """Retrieve a pair by its ID."""
        pass

    @abstractmethod
    async def create(self, pair: Pair) -> Pair:
        """Create a new pair."""
        pass

    @abstractmethod
    async def update(self, pair: Pair) -> Optional[Pair]:
        """Update an existing pair."""
        pass

    @abstractmethod
    async def delete(self, pair_id: str) -> bool:
        """Delete a pair by ID."""
        pass

    @abstractmethod
    async def delete_all(self) -> int:
        """Delete all pairs and return count of deleted items."""
        pass


class ISearchEngine(ABC):
    """Abstract interface for search functionality."""

    @abstractmethod
    async def index_pair(self, pair: Pair) -> None:
        """Index a pair for searching."""
        pass

    @abstractmethod
    async def search_pairs(self, query: str) -> List[str]:
        """Search pairs and return list of IDs."""
        pass

    @abstractmethod
    async def delete_pair_index(self, pair_id: str) -> None:
        """Remove pair from search index."""
        pass

    @abstractmethod
    async def delete_all_indices(self) -> None:
        """Clear all search indices."""
        pass


class IUserRepository(ABC):
    """Abstract repository interface for User entities."""

    @abstractmethod
    async def get_by_id(self, user_id: str) -> Optional[User]:
        """Retrieve a user by ID."""
        pass

    @abstractmethod
    async def get_by_email(self, email: str) -> Optional[User]:
        """Retrieve a user by email."""
        pass

    @abstractmethod
    async def get_by_username(self, username: str) -> Optional[User]:
        """Retrieve a user by username."""
        pass

    @abstractmethod
    async def create(self, user: User) -> User:
        """Create a new user."""
        pass

    @abstractmethod
    async def update(self, user: User) -> Optional[User]:
        """Update an existing user."""
        pass

    @abstractmethod
    async def update_energy(self, user_id: str, energy_delta: int) -> bool:
        """Atomically update user energy by delta."""
        pass

    @abstractmethod
    async def recharge_energy(self, user_id: str) -> bool:
        """Recharge user energy to max if new day started."""
        pass


class IPasswordHandler(ABC):
    """Abstract interface for password hashing and verification."""

    @abstractmethod
    def hash_password(self, password: str, salt: Optional[str] = None) -> tuple[str, str]:
        """Hash a password with salt. Returns (hash, salt)."""
        pass

    @abstractmethod
    def verify_password(self, password: str, password_hash: str, salt: str) -> bool:
        """Verify a password against stored hash and salt."""
        pass


class IJWTHandler(ABC):
    """Abstract interface for JWT token operations."""

    @abstractmethod
    def encode(self, payload: dict) -> str:
        """Encode payload into JWT token."""
        pass

    @abstractmethod
    def decode(self, token: str) -> dict:
        """Decode and verify JWT token. Raises exception if invalid."""
        pass
