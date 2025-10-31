"""MongoDB implementation of repository."""
from typing import Optional
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from datetime import datetime

from domain.entities import User
from domain.interfaces import IUserRepository


class MongoDBConnection:
    """MongoDB connection manager."""

    def __init__(self, url: str, db_name: str):
        """Initialize connection parameters."""
        self.url = url
        self.db_name = db_name
        self.client: Optional[AsyncIOMotorClient] = None
        self.db: Optional[AsyncIOMotorDatabase] = None

    async def connect(self):
        """Establish connection to MongoDB."""
        self.client = AsyncIOMotorClient(self.url)
        self.db = self.client[self.db_name]
        # Test connection
        await self.client.admin.command('ping')
        print(f"Connected to MongoDB: {self.db_name}")

    async def disconnect(self):
        """Close MongoDB connection."""
        if self.client:
            self.client.close()
            print("Disconnected from MongoDB")

    def get_database(self) -> AsyncIOMotorDatabase:
        """Get database instance."""
        if self.db is None:
            raise RuntimeError("Database not connected")
        return self.db


class MongoDBUserRepository(IUserRepository):
    """MongoDB implementation of IUserRepository."""

    def __init__(self, db: AsyncIOMotorDatabase):
        """Initialize with MongoDB database instance."""
        self.db = db
        self.collection = db["users"]
        # Create indexes
        self._ensure_indexes()

    def _ensure_indexes(self):
        """Ensure indexes are created (non-blocking)."""
        async def create_indexes():
            try:
                await self.collection.create_index(
                    [("email", 1)],
                    name="email_unique",
                    unique=True,
                    sparse=True
                )
                await self.collection.create_index(
                    [("username", 1)],
                    name="username_unique",
                    unique=True,
                    sparse=True
                )
            except Exception:
                pass

        # Schedule index creation
        import asyncio
        asyncio.create_task(create_indexes())

    async def get_by_id(self, user_id: str) -> Optional[User]:
        """Retrieve a user by ID."""
        document = await self.collection.find_one({"_id": user_id})
        return self._document_to_entity(document) if document else None

    async def get_by_email(self, email: str) -> Optional[User]:
        """Retrieve a user by email."""
        document = await self.collection.find_one({"email": email.lower()})
        return self._document_to_entity(document) if document else None

    async def get_by_username(self, username: str) -> Optional[User]:
        """Retrieve a user by username."""
        document = await self.collection.find_one({"username": username})
        return self._document_to_entity(document) if document else None

    async def create(self, user: User) -> User:
        """Create a new user."""
        document = self._entity_to_document(user)
        await self.collection.insert_one(document)
        return user

    async def update(self, user: User) -> Optional[User]:
        """Update an existing user."""
        document = self._entity_to_document(user)
        result = await self.collection.replace_one(
            {"_id": user.id},
            document
        )
        return user if result.modified_count > 0 else None

    async def update_energy(self, user_id: str, energy_delta: int) -> bool:
        """Atomically update user energy by delta."""
        result = await self.collection.update_one(
            {"_id": user_id, "energy": {"$gte": abs(energy_delta) if energy_delta < 0 else 0}},
            {"$inc": {"energy": energy_delta}}
        )
        return result.modified_count > 0

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
        result = await self.collection.update_one(
            {"_id": user_id},
            {
                "$set": {
                    "energy": user.max_energy,
                    "last_recharge": now
                }
            }
        )
        return result.modified_count > 0

    @staticmethod
    def _entity_to_document(user: User) -> dict:
        """Convert domain entity to MongoDB document."""
        return {
            "_id": user.id,
            "username": user.username,
            "email": user.email,
            "password_hash": user.password_hash,
            "salt": user.salt,
            "created_at": user.created_at,
            "energy": user.energy,
            "max_energy": user.max_energy,
            "level": user.level,
            "xp": user.xp,
            "role": user.role,
            "last_recharge": user.last_recharge
        }

    @staticmethod
    def _document_to_entity(document: dict) -> User:
        """Convert MongoDB document to domain entity."""
        return User(
            id=document["_id"],
            username=document["username"],
            email=document["email"],
            password_hash=document["password_hash"],
            salt=document["salt"],
            created_at=document.get("created_at"),
            energy=document.get("energy", 10),
            max_energy=document.get("max_energy", 10),
            level=document.get("level", 1),
            xp=document.get("xp", 0),
            role=document.get("role", "user"),
            last_recharge=document.get("last_recharge")
        )
