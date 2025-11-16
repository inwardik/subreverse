"""SQLAlchemy models for PostgreSQL database."""
from datetime import datetime
from typing import Optional
from sqlalchemy import String, Integer, DateTime, Text, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from uuid import uuid4


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""
    pass


class UserModel(Base):
    """SQLAlchemy model for User table."""
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    username: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    salt: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    energy: Mapped[int] = mapped_column(Integer, nullable=False, default=10)
    max_energy: Mapped[int] = mapped_column(Integer, nullable=False, default=10)
    level: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    xp: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    role: Mapped[str] = mapped_column(String(50), nullable=False, default="user")
    last_recharge: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)

    def __repr__(self) -> str:
        return f"<UserModel(id={self.id}, username={self.username}, email={self.email})>"


class IdiomModel(Base):
    """SQLAlchemy model for Idiom table."""
    __tablename__ = "idioms"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    title: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    en: Mapped[str] = mapped_column(Text, nullable=False)
    ru: Mapped[str] = mapped_column(Text, nullable=False)
    explanation: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    source: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="draft", index=True)
    ai_score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    likes: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    dislikes: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self) -> str:
        return f"<IdiomModel(id={self.id}, user_id={self.user_id}, en={self.en[:30]}..., status={self.status})>"


class IdiomLikeModel(Base):
    """SQLAlchemy model for IdiomLike table."""
    __tablename__ = "idiom_likes"
    __table_args__ = (
        UniqueConstraint('user_id', 'idiom_id', name='uq_user_idiom'),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    idiom_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    type: Mapped[str] = mapped_column(String(10), nullable=False)  # "like" or "dislike"
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self) -> str:
        return f"<IdiomLikeModel(id={self.id}, user_id={self.user_id}, idiom_id={self.idiom_id}, type={self.type})>"
