"""Test configuration and fixtures."""
import os
import asyncio
from typing import AsyncGenerator
import pytest
import pytest_asyncio
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from httpx import AsyncClient

# Add src to path for imports
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.api.main import app
from src.infrastructure.database.postgres import PostgreSQLConnection, PostgreSQLUserRepository
from src.infrastructure.database.postgres_models import Base
from src.infrastructure.database.mongodb import MongoDBConnection
from src.infrastructure.database.subtitle_mongo_repo import (
    MongoDBSubtitlePairRepository,
    MongoDBIdiomRepository,
    MongoDBQuoteRepository,
    MongoDBStatsRepository
)
from src.infrastructure.security.password import SHA256PasswordHandler
from src.infrastructure.security.jwt_handler import ManualJWTHandler
from src.application.auth_service import AuthService
from src.application.subtitle_service import SubtitlePairService


# Test database URLs
TEST_POSTGRES_URL = os.getenv(
    "TEST_POSTGRES_URL",
    "postgresql+asyncpg://subreverse:subreverse@localhost:5432/subreverse_test"
)
TEST_MONGODB_URL = os.getenv(
    "TEST_MONGODB_URL",
    "mongodb://localhost:27017"
)
TEST_MONGODB_DB = "subreverse_test"
JWT_SECRET = "test_secret_key_for_testing_only"


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# PostgreSQL fixtures
@pytest_asyncio.fixture
async def postgres_engine():
    """Create test PostgreSQL engine."""
    engine = create_async_engine(
        TEST_POSTGRES_URL,
        echo=False,
        pool_pre_ping=True
    )

    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    # Drop all tables after tests
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest_asyncio.fixture
async def postgres_session(postgres_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create test PostgreSQL session."""
    async_session_maker = async_sessionmaker(
        postgres_engine,
        class_=AsyncSession,
        expire_on_commit=False
    )

    async with async_session_maker() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture
async def postgres_user_repo(postgres_session):
    """Create PostgreSQL user repository."""
    return PostgreSQLUserRepository(postgres_session)


# MongoDB fixtures
@pytest_asyncio.fixture
async def mongodb_client():
    """Create test MongoDB client."""
    client = AsyncIOMotorClient(TEST_MONGODB_URL)
    yield client

    # Clean up test database
    await client.drop_database(TEST_MONGODB_DB)
    client.close()


@pytest_asyncio.fixture
async def mongodb_db(mongodb_client) -> AsyncIOMotorDatabase:
    """Create test MongoDB database."""
    db = mongodb_client[TEST_MONGODB_DB]

    # Create indexes
    await db.pairs.create_index("seq_id", unique=True, sparse=True)
    await db.pairs.create_index([("en", 1)])
    await db.pairs.create_index([("ru", 1)])
    await db.pairs.create_index([("file_en", 1)])
    await db.pairs.create_index([("category", 1)])

    yield db

    # Clean all collections after each test
    await db.pairs.delete_many({})
    await db.idioms.delete_many({})
    await db.quotes.delete_many({})
    await db.system_stats.delete_many({})


@pytest_asyncio.fixture
async def mongo_subtitle_repo(mongodb_db):
    """Create MongoDB subtitle repository."""
    return MongoDBSubtitlePairRepository(mongodb_db)


@pytest_asyncio.fixture
async def mongo_idiom_repo(mongodb_db):
    """Create MongoDB idiom repository."""
    return MongoDBIdiomRepository(mongodb_db)


@pytest_asyncio.fixture
async def mongo_quote_repo(mongodb_db):
    """Create MongoDB quote repository."""
    return MongoDBQuoteRepository(mongodb_db)


@pytest_asyncio.fixture
async def mongo_stats_repo(mongodb_db):
    """Create MongoDB stats repository."""
    return MongoDBStatsRepository(mongodb_db)


# Security fixtures
@pytest.fixture
def password_handler():
    """Create password handler."""
    return SHA256PasswordHandler()


@pytest.fixture
def jwt_handler():
    """Create JWT handler."""
    return ManualJWTHandler(JWT_SECRET, "HS256")


# Service fixtures
@pytest_asyncio.fixture
async def auth_service(postgres_user_repo, password_handler, jwt_handler):
    """Create authentication service."""
    return AuthService(
        user_repository=postgres_user_repo,
        password_handler=password_handler,
        jwt_handler=jwt_handler,
        jwt_expire_seconds=3600  # 1 hour for tests
    )


@pytest_asyncio.fixture
async def subtitle_service(
    mongo_subtitle_repo,
    mongo_idiom_repo,
    mongo_quote_repo,
    mongo_stats_repo,
    postgres_user_repo
):
    """Create subtitle service."""
    return SubtitlePairService(
        pair_repository=mongo_subtitle_repo,
        idiom_repository=mongo_idiom_repo,
        quote_repository=mongo_quote_repo,
        stats_repository=mongo_stats_repo,
        user_repository=postgres_user_repo,
        search_engine=None  # No Elasticsearch in tests
    )


# HTTP client fixtures
@pytest_asyncio.fixture
async def async_client() -> AsyncGenerator[AsyncClient, None]:
    """Create async HTTP client for testing API endpoints."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client


# Helper fixtures
@pytest_asyncio.fixture
async def test_user(auth_service):
    """Create a test user."""
    from src.application.dto import SignupDTO

    signup_data = SignupDTO(
        username="testuser",
        email="test@example.com",
        password="testpassword123"
    )

    result = await auth_service.signup(signup_data)
    return result


@pytest_asyncio.fixture
async def test_user_token(test_user):
    """Get test user token."""
    return test_user.token


@pytest_asyncio.fixture
async def authenticated_client(async_client, test_user_token) -> AsyncClient:
    """Create authenticated HTTP client."""
    async_client.headers.update({"Authorization": f"Bearer {test_user_token}"})
    return async_client
