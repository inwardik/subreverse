"""Dependency injection container for FastAPI."""
from fastapi import Depends, HTTPException, status, Header
from typing import AsyncGenerator, Optional

from infrastructure.config import settings
from infrastructure.database.mongodb import (
    MongoDBUserRepository,
    MongoDBConnection
)
from infrastructure.database.postgres import (
    PostgreSQLUserRepository,
    PostgreSQLIdiomRepository,
    PostgreSQLIdiomLikeRepository,
    PostgreSQLConnection
)
from infrastructure.database.subtitle_mongo_repo import (
    MongoDBSubtitlePairRepository,
    MongoDBIdiomRepository,
    MongoDBQuoteRepository,
    MongoDBStatsRepository
)
from infrastructure.security.password import PasswordHandler
from infrastructure.security.jwt_handler import JWTHandler
from domain.interfaces import (
    IUserRepository,
    IPasswordHandler,
    IJWTHandler,
    ISubtitlePairRepository,
    IIdiomRepository,
    IIdiomLikeRepository,
    IQuoteRepository,
    IStatsRepository,
    ISearchEngine
)
from domain.entities import User
from application.auth_service import AuthService
from application.subtitle_service import SubtitlePairService
from infrastructure.elasticsearch_engine import ElasticsearchEngine


# Global connection instances
_mongodb_connection: MongoDBConnection = None
_postgres_connection: PostgreSQLConnection = None
_elasticsearch_engine: Optional[ISearchEngine] = None


async def init_connections():
    """Initialize all database connections on startup."""
    global _mongodb_connection, _postgres_connection, _elasticsearch_engine

    # Initialize MongoDB
    _mongodb_connection = MongoDBConnection(
        url=settings.MONGODB_URL,
        db_name=settings.MONGODB_DB_NAME
    )
    await _mongodb_connection.connect()

    # Initialize PostgreSQL
    _postgres_connection = PostgreSQLConnection(
        database_url=settings.POSTGRES_URL
    )
    await _postgres_connection.init_db()

    # Initialize Elasticsearch (optional)
    if settings.ELASTICSEARCH_URL:
        try:
            _elasticsearch_engine = ElasticsearchEngine(
                es_url=settings.ELASTICSEARCH_URL,
                index_name=settings.ELASTICSEARCH_INDEX
            )
        except Exception:
            # Elasticsearch is optional, so we continue without it
            _elasticsearch_engine = None


async def close_connections():
    """Close all database connections on shutdown."""
    global _mongodb_connection, _postgres_connection, _elasticsearch_engine

    if _mongodb_connection:
        await _mongodb_connection.disconnect()

    if _postgres_connection:
        await _postgres_connection.close()

    if _elasticsearch_engine:
        await _elasticsearch_engine.close()


# Auth dependencies

async def get_user_repository() -> AsyncGenerator[IUserRepository, None]:
    """Dependency injection for user repository."""
    if not _postgres_connection:
        raise RuntimeError("PostgreSQL connection not initialized")

    async for session in _postgres_connection.get_session():
        yield PostgreSQLUserRepository(session)


def get_password_handler() -> IPasswordHandler:
    """Dependency injection for password handler."""
    return PasswordHandler()


def get_jwt_handler() -> IJWTHandler:
    """Dependency injection for JWT handler."""
    return JWTHandler(
        secret=settings.JWT_SECRET,
        algorithm=settings.JWT_ALGORITHM
    )


async def get_auth_service(
    user_repository: IUserRepository = Depends(get_user_repository),
    password_handler: IPasswordHandler = Depends(get_password_handler),
    jwt_handler: IJWTHandler = Depends(get_jwt_handler)
) -> AuthService:
    """Dependency injection for AuthService."""
    return AuthService(
        user_repository=user_repository,
        password_handler=password_handler,
        jwt_handler=jwt_handler,
        jwt_expire_seconds=settings.JWT_EXPIRE_SECONDS
    )


async def get_current_user(
    authorization: Optional[str] = Header(default=None),
    auth_service: AuthService = Depends(get_auth_service)
) -> Optional[User]:
    """
    Dependency to get current authenticated user from JWT token.

    Args:
        authorization: Authorization header (Bearer <token>)
        auth_service: Auth service for token verification

    Returns:
        User entity if authenticated, None otherwise

    Raises:
        HTTPException 401: If token is invalid or expired
    """
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )

    try:
        # Extract token from "Bearer <token>"
        scheme, token = authorization.split(" ", 1)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header format"
        )

    if scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication scheme"
        )

    # Verify token and get user
    user = await auth_service.verify_token(token)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )

    return user


async def get_current_user_optional(
    authorization: Optional[str] = Header(default=None),
    auth_service: AuthService = Depends(get_auth_service)
) -> Optional[User]:
    """
    Optional dependency to get current user without raising exception.

    Returns None if not authenticated instead of raising HTTPException.
    """
    if not authorization:
        return None

    try:
        scheme, token = authorization.split(" ", 1)
        if scheme.lower() != "bearer":
            return None

        user = await auth_service.verify_token(token)
        return user
    except Exception:
        return None


async def get_admin_user(
    user: User = Depends(get_current_user)
) -> User:
    """
    Dependency to verify that current user has admin role.

    Args:
        user: Current authenticated user

    Returns:
        User entity if user is an admin

    Raises:
        HTTPException 403: If user does not have admin role
    """
    if user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return user


# Subtitle service dependencies

async def get_subtitle_pair_repository() -> ISubtitlePairRepository:
    """Dependency injection for subtitle pair repository."""
    if not _mongodb_connection:
        raise RuntimeError("MongoDB connection not initialized")
    db = _mongodb_connection.get_database()
    return MongoDBSubtitlePairRepository(db)


async def get_idiom_repository() -> AsyncGenerator[IIdiomRepository, None]:
    """Dependency injection for idiom repository."""
    if not _postgres_connection:
        raise RuntimeError("PostgreSQL connection not initialized")

    async for session in _postgres_connection.get_session():
        yield PostgreSQLIdiomRepository(session)


async def get_idiom_like_repository() -> AsyncGenerator[IIdiomLikeRepository, None]:
    """Dependency injection for idiom like repository."""
    if not _postgres_connection:
        raise RuntimeError("PostgreSQL connection not initialized")

    async for session in _postgres_connection.get_session():
        yield PostgreSQLIdiomLikeRepository(session)


async def get_quote_repository() -> IQuoteRepository:
    """Dependency injection for quote repository."""
    if not _mongodb_connection:
        raise RuntimeError("MongoDB connection not initialized")
    db = _mongodb_connection.get_database()
    return MongoDBQuoteRepository(db)


async def get_stats_repository() -> IStatsRepository:
    """Dependency injection for stats repository."""
    if not _mongodb_connection:
        raise RuntimeError("MongoDB connection not initialized")
    db = _mongodb_connection.get_database()
    return MongoDBStatsRepository(db)


async def get_search_engine() -> Optional[ISearchEngine]:
    """Dependency injection for search engine (optional)."""
    return _elasticsearch_engine


async def get_subtitle_service(
    pair_repo: ISubtitlePairRepository = Depends(get_subtitle_pair_repository),
    idiom_repo: IIdiomRepository = Depends(get_idiom_repository),
    idiom_like_repo: IIdiomLikeRepository = Depends(get_idiom_like_repository),
    quote_repo: IQuoteRepository = Depends(get_quote_repository),
    stats_repo: IStatsRepository = Depends(get_stats_repository),
    user_repo: IUserRepository = Depends(get_user_repository),
    search_engine: Optional[ISearchEngine] = Depends(get_search_engine)
) -> SubtitlePairService:
    """Dependency injection for SubtitlePairService."""
    return SubtitlePairService(
        pair_repo=pair_repo,
        idiom_repo=idiom_repo,
        idiom_like_repo=idiom_like_repo,
        quote_repo=quote_repo,
        stats_repo=stats_repo,
        user_repo=user_repo,
        search_engine=search_engine
    )
