"""Dependency injection container for FastAPI."""
from fastapi import Depends, HTTPException, status, Header
from typing import AsyncGenerator, Optional

from infrastructure.config import settings
from infrastructure.database.mongodb import (
    MongoDBPairRepository,
    MongoDBUserRepository,
    MongoDBConnection
)
from infrastructure.database.postgresql import (
    PostgreSQLPairRepository,
    PostgreSQLUserRepository,
    PostgreSQLConnection
)
from infrastructure.database.elasticsearch import ElasticsearchEngine, ElasticsearchConnection
from infrastructure.security.password import PasswordHandler
from infrastructure.security.jwt_handler import JWTHandler
from domain.interfaces import (
    IPairRepository,
    ISearchEngine,
    IUserRepository,
    IPasswordHandler,
    IJWTHandler
)
from domain.entities import User
from application.services import PairService
from application.auth_service import AuthService


# Global connection instances
_mongodb_connection: MongoDBConnection = None
_postgresql_connection: PostgreSQLConnection = None
_elasticsearch_connection: ElasticsearchConnection = None


async def init_connections():
    """Initialize all database connections on startup."""
    global _mongodb_connection, _postgresql_connection, _elasticsearch_connection

    # Initialize Elasticsearch (used by both DB types)
    _elasticsearch_connection = ElasticsearchConnection(
        url=settings.ELASTICSEARCH_URL,
        index_name=settings.ELASTICSEARCH_INDEX
    )
    await _elasticsearch_connection.connect()

    # Initialize primary database based on configuration
    if settings.DATABASE_TYPE == "mongodb":
        _mongodb_connection = MongoDBConnection(
            url=settings.MONGODB_URL,
            db_name=settings.MONGODB_DB_NAME
        )
        await _mongodb_connection.connect()
    else:  # postgresql
        _postgresql_connection = PostgreSQLConnection(
            url=settings.POSTGRESQL_URL
        )
        await _postgresql_connection.connect()


async def close_connections():
    """Close all database connections on shutdown."""
    global _mongodb_connection, _postgresql_connection, _elasticsearch_connection

    if _elasticsearch_connection:
        await _elasticsearch_connection.disconnect()

    if _mongodb_connection:
        await _mongodb_connection.disconnect()

    if _postgresql_connection:
        await _postgresql_connection.disconnect()


async def get_repository() -> IPairRepository:
    """Dependency injection for repository - returns implementation based on config."""
    if settings.DATABASE_TYPE == "mongodb":
        if not _mongodb_connection:
            raise RuntimeError("MongoDB connection not initialized")
        db = _mongodb_connection.get_database()
        return MongoDBPairRepository(db)
    else:  # postgresql
        if not _postgresql_connection:
            raise RuntimeError("PostgreSQL connection not initialized")
        session = await _postgresql_connection.get_session()
        return PostgreSQLPairRepository(session)


async def get_search_engine() -> ISearchEngine:
    """Dependency injection for search engine."""
    if not _elasticsearch_connection:
        raise RuntimeError("Elasticsearch connection not initialized")
    client = _elasticsearch_connection.get_client()
    return ElasticsearchEngine(client, settings.ELASTICSEARCH_INDEX)


async def get_pair_service(
    repository: IPairRepository = Depends(get_repository),
    search_engine: ISearchEngine = Depends(get_search_engine)
) -> PairService:
    """Dependency injection for PairService."""
    return PairService(repository, search_engine)


# Auth dependencies

async def get_user_repository() -> IUserRepository:
    """Dependency injection for user repository - returns implementation based on config."""
    if settings.DATABASE_TYPE == "mongodb":
        if not _mongodb_connection:
            raise RuntimeError("MongoDB connection not initialized")
        db = _mongodb_connection.get_database()
        return MongoDBUserRepository(db)
    else:  # postgresql
        if not _postgresql_connection:
            raise RuntimeError("PostgreSQL connection not initialized")
        session = await _postgresql_connection.get_session()
        return PostgreSQLUserRepository(session)


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
