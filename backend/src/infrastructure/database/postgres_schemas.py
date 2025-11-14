"""Pydantic schemas for PostgreSQL models."""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field, ConfigDict


class UserCreateSchema(BaseModel):
    """Schema for creating a new user."""
    username: str = Field(..., min_length=3, max_length=100)
    email: EmailStr
    password_hash: str
    salt: str


class UserUpdateSchema(BaseModel):
    """Schema for updating user fields."""
    energy: Optional[int] = None
    max_energy: Optional[int] = None
    level: Optional[int] = None
    xp: Optional[int] = None
    last_recharge: Optional[datetime] = None


class UserSchema(BaseModel):
    """Schema for User model (complete representation)."""
    model_config = ConfigDict(from_attributes=True)

    id: str
    username: str
    email: str
    password_hash: str
    salt: str
    created_at: datetime
    energy: int
    max_energy: int
    level: int
    xp: int
    role: str
    last_recharge: datetime
