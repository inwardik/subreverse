"""Repository interfaces - abstractions for data access."""
from abc import ABC, abstractmethod
from typing import List, Optional
from .entities import SubtitlePair, User, Idiom, Quote, SystemStats


class ISubtitlePairRepository(ABC):
    """Abstract repository interface for SubtitlePair entities."""

    @abstractmethod
    async def get_all(self) -> List[SubtitlePair]:
        """Retrieve all subtitle pairs from storage."""
        pass

    @abstractmethod
    async def get_by_id(self, pair_id: str) -> Optional[SubtitlePair]:
        """Retrieve a subtitle pair by its ID."""
        pass

    @abstractmethod
    async def get_by_seq_id(self, seq_id: int) -> Optional[SubtitlePair]:
        """Retrieve a subtitle pair by its sequence ID."""
        pass

    @abstractmethod
    async def get_random(self) -> Optional[SubtitlePair]:
        """Retrieve a random subtitle pair."""
        pass

    @abstractmethod
    async def get_neighbor(self, pair_id: str, offset: int) -> Optional[SubtitlePair]:
        """Get neighbor pair by offset (temporal navigation within same file)."""
        pass

    @abstractmethod
    async def create(self, pair: SubtitlePair) -> SubtitlePair:
        """Create a new subtitle pair."""
        pass

    @abstractmethod
    async def create_many(self, pairs: List[SubtitlePair]) -> int:
        """Create many subtitle pairs. Returns count inserted."""
        pass

    @abstractmethod
    async def update(self, pair: SubtitlePair) -> Optional[SubtitlePair]:
        """Update an existing subtitle pair."""
        pass

    @abstractmethod
    async def update_rating(self, pair_id: str, delta: int) -> Optional[SubtitlePair]:
        """Update rating by delta. Returns updated pair."""
        pass

    @abstractmethod
    async def update_category(self, pair_id: str, category: Optional[str]) -> Optional[SubtitlePair]:
        """Update category. Returns updated pair."""
        pass

    @abstractmethod
    async def delete(self, pair_id: str) -> bool:
        """Delete a subtitle pair by ID."""
        pass

    @abstractmethod
    async def delete_all(self) -> int:
        """Delete all subtitle pairs and return count of deleted items."""
        pass

    @abstractmethod
    async def clear_duplicates(self) -> int:
        """Remove duplicate pairs. Returns count deleted."""
        pass

    @abstractmethod
    async def count_total(self) -> int:
        """Count total number of pairs."""
        pass

    @abstractmethod
    async def get_distinct_files_en(self) -> List[str]:
        """Get list of distinct en filenames."""
        pass


class ISearchEngine(ABC):
    """Abstract interface for search functionality."""

    @abstractmethod
    async def index_pair(self, pair: SubtitlePair) -> None:
        """Index a pair for searching."""
        pass

    @abstractmethod
    async def index_many(self, pairs: List[SubtitlePair]) -> int:
        """Index many pairs. Returns count indexed."""
        pass

    @abstractmethod
    async def search_pairs(self, query: str, limit: int = 100) -> List[str]:
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

    @abstractmethod
    async def reindex_all(self, pairs: List[SubtitlePair]) -> int:
        """Reindex all pairs. Returns count indexed."""
        pass


class IIdiomRepository(ABC):
    """Abstract repository interface for Idiom entities."""

    @abstractmethod
    async def get_recent(self, limit: int = 10) -> List[Idiom]:
        """Get most recent idioms."""
        pass

    @abstractmethod
    async def upsert(self, idiom: Idiom) -> Idiom:
        """Insert or update idiom."""
        pass


class IQuoteRepository(ABC):
    """Abstract repository interface for Quote entities."""

    @abstractmethod
    async def get_recent(self, limit: int = 10) -> List[Quote]:
        """Get most recent quotes."""
        pass

    @abstractmethod
    async def upsert(self, quote: Quote) -> Quote:
        """Insert or update quote."""
        pass


class IStatsRepository(ABC):
    """Abstract repository interface for SystemStats."""

    @abstractmethod
    async def get_latest(self) -> Optional[SystemStats]:
        """Get latest stats."""
        pass

    @abstractmethod
    async def save(self, stats: SystemStats) -> SystemStats:
        """Save/update stats."""
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
