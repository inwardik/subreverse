"""Pydantic schemas for PostgreSQL models."""
from datetime import datetime
from typing import Optional, Literal
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


class IdiomCreateSchema(BaseModel):
    """Schema for creating a new idiom."""
    user_id: str = Field(..., min_length=1)
    en: str = Field(..., min_length=1)
    ru: str = Field(..., min_length=1)
    title: Optional[str] = None
    explanation: Optional[str] = None
    source: Optional[str] = None
    status: Literal["draft", "published", "deleted"] = "draft"
    ai_mark: Optional[int] = None


class IdiomUpdateSchema(BaseModel):
    """Schema for updating idiom fields."""
    title: Optional[str] = None
    en: Optional[str] = None
    ru: Optional[str] = None
    explanation: Optional[str] = None
    source: Optional[str] = None
    status: Optional[Literal["draft", "published", "deleted"]] = None
    ai_mark: Optional[int] = None


class IdiomSchema(BaseModel):
    """Schema for Idiom model (complete representation)."""
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str
    title: Optional[str]
    en: str
    ru: str
    explanation: Optional[str]
    source: Optional[str]
    status: str
    ai_mark: Optional[int]
    created_at: datetime
    updated_at: datetime
