"""Data Transfer Objects for API communication."""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class PairCreateDTO(BaseModel):
    """DTO for creating a new pair."""
    field1: str = Field(..., min_length=1, description="First field of the pair")
    field2: int = Field(..., ge=0, description="Second field of the pair")


class PairUpdateDTO(BaseModel):
    """DTO for updating a pair."""
    field1: Optional[str] = Field(None, min_length=1)
    field2: Optional[int] = Field(None, ge=0)


class PairResponseDTO(BaseModel):
    """DTO for pair response."""
    id: str
    field1: str
    field2: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class DeleteResponseDTO(BaseModel):
    """DTO for delete operations response."""
    deleted_count: int
    message: str


# Auth DTOs

class SignupDTO(BaseModel):
    """DTO for user registration."""
    username: str = Field(..., min_length=3, max_length=50)
    email: str = Field(..., min_length=5, max_length=100)
    password: str = Field(..., min_length=6, max_length=100)


class LoginDTO(BaseModel):
    """DTO for user login."""
    login: str = Field(..., description="Email or username")
    password: str = Field(..., min_length=6)


class UserResponseDTO(BaseModel):
    """DTO for user response (safe subset without sensitive data)."""
    id: str
    username: str
    email: str
    energy: int
    max_energy: int
    level: int
    xp: int
    role: str = "user"
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class TokenResponseDTO(BaseModel):
    """DTO for authentication response with token."""
    token: str
    user: UserResponseDTO


class SelfResponseDTO(BaseModel):
    """DTO for /self endpoint with additional fields."""
    id: str
    username: str
    email: str
    energy: int
    max_energy: int
    level: int
    xp: int
    max_xp: int
    role: str = "user"
