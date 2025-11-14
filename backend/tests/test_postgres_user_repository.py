"""Tests for PostgreSQL User Repository."""
import pytest
from datetime import datetime, timedelta
from src.domain.entities import User


@pytest.mark.asyncio
class TestPostgreSQLUserRepository:
    """Test PostgreSQL user repository operations."""

    async def test_create_user(self, postgres_user_repo):
        """Test creating a new user."""
        user = User(
            id="test-user-1",
            username="john_doe",
            email="john@example.com",
            password_hash="hashed_password",
            salt="random_salt",
            created_at=datetime.utcnow(),
            energy=10,
            max_energy=10,
            level=1,
            xp=0,
            role="user",
            last_recharge=datetime.utcnow()
        )

        created = await postgres_user_repo.create(user)

        assert created is not None
        assert created.id == user.id
        assert created.username == "john_doe"
        assert created.email == "john@example.com"
        assert created.energy == 10
        assert created.level == 1

    async def test_get_user_by_id(self, postgres_user_repo):
        """Test retrieving user by ID."""
        # Create user
        user = User(
            id="test-user-2",
            username="jane_doe",
            email="jane@example.com",
            password_hash="hashed_password",
            salt="random_salt",
            created_at=datetime.utcnow(),
            energy=10,
            max_energy=10,
            level=1,
            xp=0,
            role="user",
            last_recharge=datetime.utcnow()
        )
        await postgres_user_repo.create(user)

        # Retrieve user
        retrieved = await postgres_user_repo.get_by_id("test-user-2")

        assert retrieved is not None
        assert retrieved.id == "test-user-2"
        assert retrieved.username == "jane_doe"
        assert retrieved.email == "jane@example.com"

    async def test_get_user_by_email(self, postgres_user_repo):
        """Test retrieving user by email."""
        user = User(
            id="test-user-3",
            username="bob_smith",
            email="bob@example.com",
            password_hash="hashed_password",
            salt="random_salt",
            created_at=datetime.utcnow(),
            energy=10,
            max_energy=10,
            level=1,
            xp=0,
            role="user",
            last_recharge=datetime.utcnow()
        )
        await postgres_user_repo.create(user)

        # Retrieve by email
        retrieved = await postgres_user_repo.get_by_email("bob@example.com")

        assert retrieved is not None
        assert retrieved.email == "bob@example.com"
        assert retrieved.username == "bob_smith"

    async def test_get_user_by_username(self, postgres_user_repo):
        """Test retrieving user by username."""
        user = User(
            id="test-user-4",
            username="alice_wonder",
            email="alice@example.com",
            password_hash="hashed_password",
            salt="random_salt",
            created_at=datetime.utcnow(),
            energy=10,
            max_energy=10,
            level=1,
            xp=0,
            role="user",
            last_recharge=datetime.utcnow()
        )
        await postgres_user_repo.create(user)

        # Retrieve by username
        retrieved = await postgres_user_repo.get_by_username("alice_wonder")

        assert retrieved is not None
        assert retrieved.username == "alice_wonder"
        assert retrieved.email == "alice@example.com"

    async def test_get_nonexistent_user(self, postgres_user_repo):
        """Test retrieving non-existent user returns None."""
        retrieved = await postgres_user_repo.get_by_id("nonexistent-id")
        assert retrieved is None

        retrieved = await postgres_user_repo.get_by_email("nonexistent@example.com")
        assert retrieved is None

        retrieved = await postgres_user_repo.get_by_username("nonexistent_user")
        assert retrieved is None

    async def test_update_user(self, postgres_user_repo):
        """Test updating user information."""
        # Create user
        user = User(
            id="test-user-5",
            username="charlie",
            email="charlie@example.com",
            password_hash="hashed_password",
            salt="random_salt",
            created_at=datetime.utcnow(),
            energy=10,
            max_energy=10,
            level=1,
            xp=0,
            role="user",
            last_recharge=datetime.utcnow()
        )
        created = await postgres_user_repo.create(user)

        # Update user
        created.energy = 5
        created.xp = 15
        created.level = 2
        updated = await postgres_user_repo.update(created)

        assert updated is not None
        assert updated.energy == 5
        assert updated.xp == 15
        assert updated.level == 2

    async def test_update_energy_positive(self, postgres_user_repo):
        """Test atomically increasing user energy."""
        # Create user
        user = User(
            id="test-user-6",
            username="david",
            email="david@example.com",
            password_hash="hashed_password",
            salt="random_salt",
            created_at=datetime.utcnow(),
            energy=5,
            max_energy=10,
            level=1,
            xp=0,
            role="user",
            last_recharge=datetime.utcnow()
        )
        await postgres_user_repo.create(user)

        # Increase energy
        success = await postgres_user_repo.update_energy("test-user-6", 3)
        assert success is True

        # Verify energy increased
        updated = await postgres_user_repo.get_by_id("test-user-6")
        assert updated.energy == 8

    async def test_update_energy_negative(self, postgres_user_repo):
        """Test atomically decreasing user energy."""
        # Create user
        user = User(
            id="test-user-7",
            username="eve",
            email="eve@example.com",
            password_hash="hashed_password",
            salt="random_salt",
            created_at=datetime.utcnow(),
            energy=10,
            max_energy=10,
            level=1,
            xp=0,
            role="user",
            last_recharge=datetime.utcnow()
        )
        await postgres_user_repo.create(user)

        # Decrease energy
        success = await postgres_user_repo.update_energy("test-user-7", -3)
        assert success is True

        # Verify energy decreased
        updated = await postgres_user_repo.get_by_id("test-user-7")
        assert updated.energy == 7

    async def test_update_energy_insufficient(self, postgres_user_repo):
        """Test that energy cannot go negative."""
        # Create user with 2 energy
        user = User(
            id="test-user-8",
            username="frank",
            email="frank@example.com",
            password_hash="hashed_password",
            salt="random_salt",
            created_at=datetime.utcnow(),
            energy=2,
            max_energy=10,
            level=1,
            xp=0,
            role="user",
            last_recharge=datetime.utcnow()
        )
        await postgres_user_repo.create(user)

        # Try to decrease by 5 (should fail)
        success = await postgres_user_repo.update_energy("test-user-8", -5)
        assert success is False

        # Verify energy unchanged
        updated = await postgres_user_repo.get_by_id("test-user-8")
        assert updated.energy == 2

    async def test_recharge_energy_new_day(self, postgres_user_repo):
        """Test energy recharge on new day."""
        # Create user with last recharge yesterday
        yesterday = datetime.utcnow() - timedelta(days=1)
        user = User(
            id="test-user-9",
            username="grace",
            email="grace@example.com",
            password_hash="hashed_password",
            salt="random_salt",
            created_at=datetime.utcnow(),
            energy=3,
            max_energy=10,
            level=1,
            xp=0,
            role="user",
            last_recharge=yesterday
        )
        await postgres_user_repo.create(user)

        # Recharge energy
        success = await postgres_user_repo.recharge_energy("test-user-9")
        assert success is True

        # Verify energy recharged
        updated = await postgres_user_repo.get_by_id("test-user-9")
        assert updated.energy == 10
        assert updated.last_recharge.date() == datetime.utcnow().date()

    async def test_recharge_energy_same_day(self, postgres_user_repo):
        """Test that energy doesn't recharge on same day."""
        # Create user with last recharge today
        user = User(
            id="test-user-10",
            username="henry",
            email="henry@example.com",
            password_hash="hashed_password",
            salt="random_salt",
            created_at=datetime.utcnow(),
            energy=5,
            max_energy=10,
            level=1,
            xp=0,
            role="user",
            last_recharge=datetime.utcnow()
        )
        await postgres_user_repo.create(user)

        # Try to recharge (should return False)
        success = await postgres_user_repo.recharge_energy("test-user-10")
        assert success is False

        # Verify energy unchanged
        updated = await postgres_user_repo.get_by_id("test-user-10")
        assert updated.energy == 5

    async def test_create_user_without_id(self, postgres_user_repo):
        """Test creating user without providing ID (auto-generated)."""
        user = User(
            id=None,  # No ID provided
            username="ivan",
            email="ivan@example.com",
            password_hash="hashed_password",
            salt="random_salt",
            created_at=datetime.utcnow(),
            energy=10,
            max_energy=10,
            level=1,
            xp=0,
            role="user",
            last_recharge=datetime.utcnow()
        )

        created = await postgres_user_repo.create(user)

        assert created is not None
        assert created.id is not None  # ID should be auto-generated
        assert created.username == "ivan"

    async def test_update_nonexistent_user(self, postgres_user_repo):
        """Test updating non-existent user returns None."""
        user = User(
            id="nonexistent-user",
            username="ghost",
            email="ghost@example.com",
            password_hash="hashed_password",
            salt="random_salt",
            created_at=datetime.utcnow(),
            energy=10,
            max_energy=10,
            level=1,
            xp=0,
            role="user",
            last_recharge=datetime.utcnow()
        )

        updated = await postgres_user_repo.update(user)
        assert updated is None
