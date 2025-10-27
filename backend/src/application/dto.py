"""Data Transfer Objects for API communication."""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class SubtitlePairResponseDTO(BaseModel):
    """DTO for subtitle pair response."""
    id: str = Field(alias="_id")
    en: str
    ru: str
    file_en: Optional[str] = None
    file_ru: Optional[str] = None
    time_en: Optional[str] = None
    time_ru: Optional[str] = None
    rating: int = 0
    category: Optional[str] = None
    seq_id: Optional[int] = None

    class Config:
        from_attributes = True
        populate_by_name = True


class SubtitlePairUpdateDTO(BaseModel):
    """DTO for updating a subtitle pair via PATCH."""
    delta: Optional[int] = Field(None, description="Rating delta (+1 or -1)")
    category: Optional[str] = Field(None, description="Category: idiom, quote, wrong, or null to unset")


class IdiomResponseDTO(BaseModel):
    """DTO for idiom response."""
    id: str = Field(alias="_id")
    en: str
    ru: str
    filename: Optional[str] = None
    time: Optional[str] = None
    owner_username: Optional[str] = None
    rating: int = 0

    class Config:
        from_attributes = True
        populate_by_name = True


class QuoteResponseDTO(BaseModel):
    """DTO for quote response."""
    id: str = Field(alias="_id")
    en: str
    ru: str
    filename: Optional[str] = None
    time: Optional[str] = None
    owner_username: Optional[str] = None
    rating: int = 0

    class Config:
        from_attributes = True
        populate_by_name = True


class StatsResponseDTO(BaseModel):
    """DTO for stats response."""
    total: int
    files_en: list[str]
    updated_at: Optional[str] = None


class DeleteResponseDTO(BaseModel):
    """DTO for delete operations response."""
    deleted_count: int
    message: str


class ClearDuplicatesResponseDTO(BaseModel):
    """DTO for clear duplicates response."""
    duplicate_groups: int
    documents_deleted: int
    documents_kept_per_group: int = 1


class UploadSummaryDTO(BaseModel):
    """DTO for file upload summary."""
    filename: str
    lines_read: Optional[int] = None
    inserted_docs: int
    skipped_lines: Optional[int] = None
    errors: list[str] = []


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
