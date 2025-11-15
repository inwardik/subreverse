"""Domain entities - core business objects."""
from dataclasses import dataclass
from typing import Optional
from datetime import datetime


@dataclass
class SubtitlePair:
    """Core domain entity representing a subtitle pair (en/ru)."""
    id: Optional[str]
    en: str
    ru: str
    file_en: Optional[str] = None
    file_ru: Optional[str] = None
    time_en: Optional[str] = None
    time_ru: Optional[str] = None
    rating: int = 0
    category: Optional[str] = None
    seq_id: Optional[int] = None

    def __post_init__(self):
        """Validate entity invariants."""
        if not self.en and not self.ru:
            raise ValueError("At least one of en or ru must be provided")


@dataclass
class Idiom:
    """Domain entity for idiom collection."""
    id: Optional[str]
    user_id: str
    en: str
    ru: str
    title: Optional[str] = None
    explanation: Optional[str] = None
    source: Optional[str] = None
    status: str = "draft"  # draft, published, deleted
    ai_mark: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


@dataclass
class Quote:
    """Domain entity for quote collection."""
    id: str
    en: str
    ru: str
    pair_seq_id: Optional[int] = None
    rating: int = 0
    filename: Optional[str] = None
    time: Optional[str] = None
    owner_username: Optional[str] = None


@dataclass
class SystemStats:
    """Domain entity for system statistics."""
    total: int
    files_en: list[str]
    updated_at: Optional[datetime] = None


@dataclass
class User:
    """Core domain entity representing a User."""
    id: str
    username: str
    email: str
    password_hash: str
    salt: str
    created_at: Optional[datetime] = None
    energy: int = 10
    max_energy: int = 10
    level: int = 1
    xp: int = 0
    role: str = "user"
    last_recharge: Optional[datetime] = None

    def __post_init__(self):
        """Validate entity invariants."""
        if not self.id:
            raise ValueError("User ID cannot be empty")
        if not self.username or len(self.username) < 3:
            raise ValueError("Username must be at least 3 characters")
        if not self.email or "@" not in self.email:
            raise ValueError("Valid email is required")
        if not self.password_hash:
            raise ValueError("Password hash cannot be empty")
        if self.energy < 0:
            raise ValueError("Energy cannot be negative")
        if self.max_energy < 0:
            raise ValueError("Max energy cannot be negative")
        if self.level < 1:
            raise ValueError("Level must be at least 1")
