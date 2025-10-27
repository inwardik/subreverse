"""Domain entities - core business objects."""
from dataclasses import dataclass
from typing import Optional
from datetime import datetime


@dataclass
class Pair:
    """Core domain entity representing a Pair."""
    id: str
    field1: str
    field2: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def __post_init__(self):
        """Validate entity invariants."""
        if not self.id:
            raise ValueError("Pair ID cannot be empty")
        if not self.field1:
            raise ValueError("Field1 cannot be empty")
        if self.field2 < 0:
            raise ValueError("Field2 must be non-negative")


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
