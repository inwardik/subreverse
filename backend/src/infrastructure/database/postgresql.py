"""PostgreSQL implementation of repository."""
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import String, Integer, DateTime, select, delete
from datetime import datetime

from domain.entities import Pair, User
from domain.interfaces import IPairRepository, IUserRepository


# SQLAlchemy models
class Base(DeclarativeBase):
    """Base class for SQLAlchemy models."""
    pass


class PairModel(Base):
    """SQLAlchemy model for Pair table."""
    __tablename__ = "pairs"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    field1: Mapped[str] = mapped_column(String, nullable=False)
    field2: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)


class UserModel(Base):
    """SQLAlchemy model for User table."""
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    username: Mapped[str] = mapped_column(String(50), nullable=False, unique=True, index=True)
    email: Mapped[str] = mapped_column(String(100), nullable=False, unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    salt: Mapped[str] = mapped_column(String(32), nullable=False)
    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    energy: Mapped[int] = mapped_column(Integer, nullable=False, default=10)
    max_energy: Mapped[int] = mapped_column(Integer, nullable=False, default=10)
    level: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    xp: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    role: Mapped[str] = mapped_column(String(20), nullable=False, default="user")
    last_recharge: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)


class PostgreSQLPairRepository(IPairRepository):
    """PostgreSQL implementation of IPairRepository."""

    def __init__(self, session: AsyncSession):
        """Initialize with SQLAlchemy async session."""
        self.session = session

    async def get_all(self) -> List[Pair]:
        """Retrieve all pairs from PostgreSQL."""
        result = await self.session.execute(select(PairModel))
        models = result.scalars().all()
        return [self._model_to_entity(model) for model in models]

    async def get_by_id(self, pair_id: str) -> Optional[Pair]:
        """Retrieve a pair by its ID."""
        result = await self.session.execute(
            select(PairModel).where(PairModel.id == pair_id)
        )
        model = result.scalar_one_or_none()
        return self._model_to_entity(model) if model else None

    async def create(self, pair: Pair) -> Pair:
        """Create a new pair."""
        model = self._entity_to_model(pair)
        self.session.add(model)
        await self.session.commit()
        await self.session.refresh(model)
        return pair

    async def update(self, pair: Pair) -> Optional[Pair]:
        """Update an existing pair."""
        result = await self.session.execute(
            select(PairModel).where(PairModel.id == pair.id)
        )
        model = result.scalar_one_or_none()

        if not model:
            return None

        model.field1 = pair.field1
        model.field2 = pair.field2
        model.updated_at = pair.updated_at

        await self.session.commit()
        await self.session.refresh(model)
        return pair

    async def delete(self, pair_id: str) -> bool:
        """Delete a pair by ID."""
        result = await self.session.execute(
            delete(PairModel).where(PairModel.id == pair_id)
        )
        await self.session.commit()
        return result.rowcount > 0

    async def delete_all(self) -> int:
        """Delete all pairs and return count."""
        result = await self.session.execute(delete(PairModel))
        await self.session.commit()
        return result.rowcount

    @staticmethod
    def _entity_to_model(pair: Pair) -> PairModel:
        """Convert domain entity to SQLAlchemy model."""
        return PairModel(
            id=pair.id,
            field1=pair.field1,
            field2=pair.field2,
            created_at=pair.created_at,
            updated_at=pair.updated_at
        )

    @staticmethod
    def _model_to_entity(model: PairModel) -> Pair:
        """Convert SQLAlchemy model to domain entity."""
        return Pair(
            id=model.id,
            field1=model.field1,
            field2=model.field2,
            created_at=model.created_at,
            updated_at=model.updated_at
        )


class PostgreSQLConnection:
    """PostgreSQL connection manager."""

    def __init__(self, url: str):
        """Initialize connection parameters."""
        self.url = url
        self.engine: Optional[AsyncEngine] = None
        self.session_maker: Optional[async_sessionmaker] = None

    async def connect(self):
        """Establish connection to PostgreSQL."""
        self.engine = create_async_engine(self.url, echo=True)

        # Create tables
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        self.session_maker = async_sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False
        )
        print("Connected to PostgreSQL")

    async def disconnect(self):
        """Close PostgreSQL connection."""
        if self.engine:
            await self.engine.dispose()
            print("Disconnected from PostgreSQL")

    async def get_session(self) -> AsyncSession:
        """Get database session."""
        if not self.session_maker:
            raise RuntimeError("Database not connected")
        return self.session_maker()


class PostgreSQLUserRepository(IUserRepository):
    """PostgreSQL implementation of IUserRepository."""

    def __init__(self, session: AsyncSession):
        """Initialize with SQLAlchemy async session."""
        self.session = session

    async def get_by_id(self, user_id: str) -> Optional[User]:
        """Retrieve a user by ID."""
        result = await self.session.execute(
            select(UserModel).where(UserModel.id == user_id)
        )
        model = result.scalar_one_or_none()
        return self._model_to_entity(model) if model else None

    async def get_by_email(self, email: str) -> Optional[User]:
        """Retrieve a user by email."""
        result = await self.session.execute(
            select(UserModel).where(UserModel.email == email.lower())
        )
        model = result.scalar_one_or_none()
        return self._model_to_entity(model) if model else None

    async def get_by_username(self, username: str) -> Optional[User]:
        """Retrieve a user by username."""
        result = await self.session.execute(
            select(UserModel).where(UserModel.username == username)
        )
        model = result.scalar_one_or_none()
        return self._model_to_entity(model) if model else None

    async def create(self, user: User) -> User:
        """Create a new user."""
        model = self._entity_to_model(user)
        self.session.add(model)
        await self.session.commit()
        await self.session.refresh(model)
        return user

    async def update(self, user: User) -> Optional[User]:
        """Update an existing user."""
        result = await self.session.execute(
            select(UserModel).where(UserModel.id == user.id)
        )
        model = result.scalar_one_or_none()

        if not model:
            return None

        # Update fields
        model.username = user.username
        model.email = user.email
        model.password_hash = user.password_hash
        model.salt = user.salt
        model.energy = user.energy
        model.max_energy = user.max_energy
        model.level = user.level
        model.xp = user.xp
        model.role = user.role
        model.last_recharge = user.last_recharge

        await self.session.commit()
        await self.session.refresh(model)
        return user

    async def update_energy(self, user_id: str, energy_delta: int) -> bool:
        """Atomically update user energy by delta."""
        from sqlalchemy import update

        result = await self.session.execute(
            update(UserModel)
            .where(UserModel.id == user_id)
            .where(UserModel.energy >= abs(energy_delta) if energy_delta < 0 else True)
            .values(energy=UserModel.energy + energy_delta)
        )
        await self.session.commit()
        return result.rowcount > 0

    async def recharge_energy(self, user_id: str) -> bool:
        """Recharge user energy to max if new day started."""
        # Get user
        user = await self.get_by_id(user_id)
        if not user:
            return False

        # Check if new day started
        now = datetime.utcnow()
        if user.last_recharge and user.last_recharge.date() >= now.date():
            # Same day, no recharge needed
            return False

        # Recharge energy
        from sqlalchemy import update

        result = await self.session.execute(
            update(UserModel)
            .where(UserModel.id == user_id)
            .values(energy=user.max_energy, last_recharge=now)
        )
        await self.session.commit()
        return result.rowcount > 0

    @staticmethod
    def _entity_to_model(user: User) -> UserModel:
        """Convert domain entity to SQLAlchemy model."""
        return UserModel(
            id=user.id,
            username=user.username,
            email=user.email,
            password_hash=user.password_hash,
            salt=user.salt,
            created_at=user.created_at,
            energy=user.energy,
            max_energy=user.max_energy,
            level=user.level,
            xp=user.xp,
            role=user.role,
            last_recharge=user.last_recharge
        )

    @staticmethod
    def _model_to_entity(model: UserModel) -> User:
        """Convert SQLAlchemy model to domain entity."""
        return User(
            id=model.id,
            username=model.username,
            email=model.email,
            password_hash=model.password_hash,
            salt=model.salt,
            created_at=model.created_at,
            energy=model.energy,
            max_energy=model.max_energy,
            level=model.level,
            xp=model.xp,
            role=model.role,
            last_recharge=model.last_recharge
        )
