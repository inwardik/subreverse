"""PostgreSQL database connection and User repository implementation."""
from datetime import datetime
from typing import Optional, List
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy import select, update, delete

from domain.entities import User, Idiom
from domain.interfaces import IUserRepository, IIdiomRepository
from infrastructure.database.postgres_models import Base, UserModel, IdiomModel


class PostgreSQLConnection:
    """PostgreSQL database connection manager."""

    def __init__(self, database_url: str):
        """Initialize PostgreSQL connection.

        Args:
            database_url: PostgreSQL connection URL (e.g., postgresql+asyncpg://user:pass@host:port/db)
        """
        self.database_url = database_url
        self.engine = create_async_engine(
            database_url,
            echo=False,
            pool_pre_ping=True,
            pool_size=10,
            max_overflow=20
        )
        self.async_session_maker = async_sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False
        )

    async def init_db(self):
        """Initialize database tables."""
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    async def close(self):
        """Close database connection."""
        await self.engine.dispose()

    async def get_session(self) -> AsyncSession:
        """Get async database session."""
        async with self.async_session_maker() as session:
            yield session


class PostgreSQLUserRepository(IUserRepository):
    """PostgreSQL implementation of User repository."""

    def __init__(self, session: AsyncSession):
        """Initialize repository with database session.

        Args:
            session: SQLAlchemy async session
        """
        self.session = session

    async def get_by_id(self, user_id: str) -> Optional[User]:
        """Retrieve a user by ID."""
        result = await self.session.execute(
            select(UserModel).where(UserModel.id == user_id)
        )
        user_model = result.scalar_one_or_none()
        return self._model_to_entity(user_model) if user_model else None

    async def get_by_email(self, email: str) -> Optional[User]:
        """Retrieve a user by email."""
        result = await self.session.execute(
            select(UserModel).where(UserModel.email == email)
        )
        user_model = result.scalar_one_or_none()
        return self._model_to_entity(user_model) if user_model else None

    async def get_by_username(self, username: str) -> Optional[User]:
        """Retrieve a user by username."""
        result = await self.session.execute(
            select(UserModel).where(UserModel.username == username)
        )
        user_model = result.scalar_one_or_none()
        return self._model_to_entity(user_model) if user_model else None

    async def create(self, user: User) -> User:
        """Create a new user."""
        user_model = UserModel(
            id=user.id or str(uuid4()),
            username=user.username,
            email=user.email,
            password_hash=user.password_hash,
            salt=user.salt,
            created_at=user.created_at or datetime.utcnow(),
            energy=user.energy,
            max_energy=user.max_energy,
            level=user.level,
            xp=user.xp,
            role=user.role,
            last_recharge=user.last_recharge or datetime.utcnow()
        )
        self.session.add(user_model)
        await self.session.commit()
        await self.session.refresh(user_model)

        # Update user entity with generated ID if it was None
        user.id = user_model.id
        return user

    async def update(self, user: User) -> Optional[User]:
        """Update an existing user."""
        result = await self.session.execute(
            select(UserModel).where(UserModel.id == user.id)
        )
        user_model = result.scalar_one_or_none()

        if not user_model:
            return None

        # Update fields
        user_model.username = user.username
        user_model.email = user.email
        user_model.password_hash = user.password_hash
        user_model.salt = user.salt
        user_model.energy = user.energy
        user_model.max_energy = user.max_energy
        user_model.level = user.level
        user_model.xp = user.xp
        user_model.role = user.role
        user_model.last_recharge = user.last_recharge

        await self.session.commit()
        await self.session.refresh(user_model)
        return self._model_to_entity(user_model)

    async def update_energy(self, user_id: str, energy_delta: int) -> bool:
        """Atomically update user energy by delta."""
        # First, get current energy to check if operation is valid
        result = await self.session.execute(
            select(UserModel.energy).where(UserModel.id == user_id)
        )
        current_energy = result.scalar_one_or_none()

        if current_energy is None:
            return False

        # Check if operation would result in negative energy
        if energy_delta < 0 and current_energy < abs(energy_delta):
            return False

        # Perform atomic update
        stmt = (
            update(UserModel)
            .where(UserModel.id == user_id)
            .values(energy=UserModel.energy + energy_delta)
        )
        result = await self.session.execute(stmt)
        await self.session.commit()

        return result.rowcount > 0

    async def recharge_energy(self, user_id: str) -> bool:
        """Recharge user energy to max if new day started."""
        user = await self.get_by_id(user_id)
        if not user:
            return False

        # Check if new day started
        now = datetime.utcnow()
        if user.last_recharge and user.last_recharge.date() >= now.date():
            # Same day, no recharge needed
            return False

        # Recharge energy
        stmt = (
            update(UserModel)
            .where(UserModel.id == user_id)
            .values(energy=user.max_energy, last_recharge=now)
        )
        result = await self.session.execute(stmt)
        await self.session.commit()

        return result.rowcount > 0

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


class PostgreSQLIdiomRepository(IIdiomRepository):
    """PostgreSQL implementation of Idiom repository."""

    def __init__(self, session: AsyncSession):
        """Initialize repository with database session.

        Args:
            session: SQLAlchemy async session
        """
        self.session = session

    async def get_all(self, limit: int = 100, status: Optional[str] = None) -> List[Idiom]:
        """Get idioms with optional status filter."""
        query = select(IdiomModel)

        if status:
            query = query.where(IdiomModel.status == status)

        query = query.order_by(IdiomModel.created_at.desc()).limit(limit)

        result = await self.session.execute(query)
        idiom_models = result.scalars().all()

        return [self._model_to_entity(model) for model in idiom_models]

    async def get_by_id(self, idiom_id: str) -> Optional[Idiom]:
        """Get idiom by ID."""
        result = await self.session.execute(
            select(IdiomModel).where(IdiomModel.id == idiom_id)
        )
        idiom_model = result.scalar_one_or_none()
        return self._model_to_entity(idiom_model) if idiom_model else None

    async def create(self, idiom: Idiom) -> Idiom:
        """Create a new idiom."""
        idiom_model = IdiomModel(
            id=idiom.id or str(uuid4()),
            user_id=idiom.user_id,
            title=idiom.title,
            en=idiom.en,
            ru=idiom.ru,
            explanation=idiom.explanation,
            source=idiom.source,
            status=idiom.status,
            ai_score=idiom.ai_score,
            created_at=idiom.created_at or datetime.utcnow(),
            updated_at=idiom.updated_at or datetime.utcnow()
        )
        self.session.add(idiom_model)
        await self.session.commit()
        await self.session.refresh(idiom_model)

        # Update idiom entity with generated ID if it was None
        idiom.id = idiom_model.id
        return idiom

    async def update(self, idiom_id: str, idiom: Idiom) -> Optional[Idiom]:
        """Update an existing idiom."""
        result = await self.session.execute(
            select(IdiomModel).where(IdiomModel.id == idiom_id)
        )
        idiom_model = result.scalar_one_or_none()

        if not idiom_model:
            return None

        # Update fields
        if idiom.title is not None:
            idiom_model.title = idiom.title
        if idiom.en:
            idiom_model.en = idiom.en
        if idiom.ru:
            idiom_model.ru = idiom.ru
        if idiom.explanation is not None:
            idiom_model.explanation = idiom.explanation
        if idiom.source is not None:
            idiom_model.source = idiom.source
        if idiom.status:
            idiom_model.status = idiom.status
        if idiom.ai_score is not None:
            idiom_model.ai_score = idiom.ai_score

        idiom_model.updated_at = datetime.utcnow()

        await self.session.commit()
        await self.session.refresh(idiom_model)
        return self._model_to_entity(idiom_model)

    async def delete(self, idiom_id: str) -> bool:
        """Delete an idiom by ID."""
        stmt = delete(IdiomModel).where(IdiomModel.id == idiom_id)
        result = await self.session.execute(stmt)
        await self.session.commit()
        return result.rowcount > 0

    async def get_for_user(self, user_id: Optional[str], limit: int = 100) -> List[Idiom]:
        """Get published idioms + user's draft idioms (user's drafts first)."""
        if user_id:
            # Get user's drafts first
            user_drafts_query = (
                select(IdiomModel)
                .where(IdiomModel.user_id == user_id)
                .where(IdiomModel.status == "draft")
                .order_by(IdiomModel.created_at.desc())
            )

            # Get published idioms (excluding deleted)
            published_query = (
                select(IdiomModel)
                .where(IdiomModel.status == "published")
                .order_by(IdiomModel.created_at.desc())
            )

            # Execute both queries
            user_drafts_result = await self.session.execute(user_drafts_query)
            user_drafts = user_drafts_result.scalars().all()

            published_result = await self.session.execute(published_query)
            published = published_result.scalars().all()

            # Combine: user's drafts first, then published
            all_idioms = list(user_drafts) + list(published)
            return [self._model_to_entity(model) for model in all_idioms[:limit]]
        else:
            # No user - only show published idioms
            query = (
                select(IdiomModel)
                .where(IdiomModel.status == "published")
                .order_by(IdiomModel.created_at.desc())
                .limit(limit)
            )
            result = await self.session.execute(query)
            idiom_models = result.scalars().all()
            return [self._model_to_entity(model) for model in idiom_models]

    @staticmethod
    def _model_to_entity(model: IdiomModel) -> Idiom:
        """Convert SQLAlchemy model to domain entity."""
        return Idiom(
            id=model.id,
            user_id=model.user_id,
            title=model.title,
            en=model.en,
            ru=model.ru,
            explanation=model.explanation,
            source=model.source,
            status=model.status,
            ai_score=model.ai_score,
            created_at=model.created_at,
            updated_at=model.updated_at
        )
