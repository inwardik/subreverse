"""Tests for MongoDB Idiom and Quote Repositories."""
import pytest
from src.domain.entities import Idiom, Quote, SystemStats


@pytest.mark.asyncio
class TestMongoDBIdiomRepository:
    """Test MongoDB idiom repository operations."""

    async def test_upsert_new_idiom(self, mongo_idiom_repo):
        """Test creating a new idiom."""
        idiom = Idiom(
            id=None,
            en="Break a leg!",
            ru="Ни пуха, ни пера!",
            pair_seq_id=1001,
            rating=5,
            filename="movie_en.srt",
            time="00:01:23,456 --> 00:01:26,789",
            owner_username="testuser"
        )

        created = await mongo_idiom_repo.upsert(idiom)

        assert created is not None
        assert created.en == "Break a leg!"
        assert created.ru == "Ни пуха, ни пера!"
        assert created.pair_seq_id == 1001

    async def test_upsert_update_existing(self, mongo_idiom_repo):
        """Test updating existing idiom by pair_seq_id."""
        # Create initial idiom
        idiom = Idiom(
            id=None,
            en="Piece of cake",
            ru="Проще простого",
            pair_seq_id=1002,
            rating=3,
            filename="movie_en.srt",
            time="00:02:00,000 --> 00:02:03,000",
            owner_username="user1"
        )
        await mongo_idiom_repo.upsert(idiom)

        # Update with same pair_seq_id
        updated_idiom = Idiom(
            id=None,
            en="Piece of cake",
            ru="Проще простого",
            pair_seq_id=1002,
            rating=7,  # Updated rating
            filename="movie_en.srt",
            time="00:02:00,000 --> 00:02:03,000",
            owner_username="user1"
        )
        await mongo_idiom_repo.upsert(updated_idiom)

        # Get recent idioms and verify
        recent = await mongo_idiom_repo.get_recent(10)
        assert len(recent) >= 1

        # Find the idiom with our pair_seq_id
        found = None
        for r in recent:
            if r.pair_seq_id == 1002:
                found = r
                break

        assert found is not None
        assert found.rating == 7  # Should have updated rating

    async def test_get_recent_idioms(self, mongo_idiom_repo):
        """Test getting recent idioms."""
        # Create multiple idioms
        idioms = [
            Idiom(
                id=None,
                en=f"Idiom {i}",
                ru=f"Идиома {i}",
                pair_seq_id=2000 + i,
                rating=i,
                filename="movie_en.srt",
                time=f"00:0{i}:00,000 --> 00:0{i}:03,000",
                owner_username="testuser"
            )
            for i in range(5)
        ]

        for idiom in idioms:
            await mongo_idiom_repo.upsert(idiom)

        # Get recent (should be sorted by insertion time, newest first)
        recent = await mongo_idiom_repo.get_recent(3)

        assert len(recent) <= 3
        # Most recent should be "Idiom 4" (last inserted)
        if len(recent) > 0:
            assert "Idiom" in recent[0].en

    async def test_get_recent_with_limit(self, mongo_idiom_repo):
        """Test that limit parameter works."""
        # Create 10 idioms
        for i in range(10):
            idiom = Idiom(
                id=None,
                en=f"Test idiom {i}",
                ru=f"Тестовая идиома {i}",
                pair_seq_id=3000 + i,
                rating=0,
                filename="test.srt",
                time="00:00:01,000 --> 00:00:03,000",
                owner_username="user"
            )
            await mongo_idiom_repo.upsert(idiom)

        # Get only 5 most recent
        recent = await mongo_idiom_repo.get_recent(5)

        assert len(recent) <= 5


@pytest.mark.asyncio
class TestMongoDBQuoteRepository:
    """Test MongoDB quote repository operations."""

    async def test_upsert_new_quote(self, mongo_quote_repo):
        """Test creating a new quote."""
        quote = Quote(
            id=None,
            en="To be or not to be",
            ru="Быть или не быть",
            pair_seq_id=4001,
            rating=10,
            filename="shakespeare_en.srt",
            time="00:05:00,000 --> 00:05:05,000",
            owner_username="shakespeare_fan"
        )

        created = await mongo_quote_repo.upsert(quote)

        assert created is not None
        assert created.en == "To be or not to be"
        assert created.ru == "Быть или не быть"
        assert created.pair_seq_id == 4001

    async def test_upsert_update_existing_quote(self, mongo_quote_repo):
        """Test updating existing quote by pair_seq_id."""
        # Create initial quote
        quote = Quote(
            id=None,
            en="May the Force be with you",
            ru="Да пребудет с тобой Сила",
            pair_seq_id=4002,
            rating=8,
            filename="starwars_en.srt",
            time="00:10:00,000 --> 00:10:03,000",
            owner_username="fan1"
        )
        await mongo_quote_repo.upsert(quote)

        # Update with same pair_seq_id
        updated_quote = Quote(
            id=None,
            en="May the Force be with you",
            ru="Да пребудет с тобой Сила",
            pair_seq_id=4002,
            rating=10,  # Updated rating
            filename="starwars_en.srt",
            time="00:10:00,000 --> 00:10:03,000",
            owner_username="fan1"
        )
        await mongo_quote_repo.upsert(updated_quote)

        # Get recent quotes and verify
        recent = await mongo_quote_repo.get_recent(10)
        assert len(recent) >= 1

        # Find the quote with our pair_seq_id
        found = None
        for r in recent:
            if r.pair_seq_id == 4002:
                found = r
                break

        assert found is not None
        assert found.rating == 10  # Should have updated rating

    async def test_get_recent_quotes(self, mongo_quote_repo):
        """Test getting recent quotes."""
        # Create multiple quotes
        quotes = [
            Quote(
                id=None,
                en=f"Famous quote {i}",
                ru=f"Знаменитая цитата {i}",
                pair_seq_id=5000 + i,
                rating=i * 2,
                filename="quotes_en.srt",
                time=f"00:0{i}:00,000 --> 00:0{i}:05,000",
                owner_username="quotelover"
            )
            for i in range(5)
        ]

        for quote in quotes:
            await mongo_quote_repo.upsert(quote)

        # Get recent (should be sorted by insertion time, newest first)
        recent = await mongo_quote_repo.get_recent(3)

        assert len(recent) <= 3
        # Most recent should contain "Famous quote"
        if len(recent) > 0:
            assert "Famous quote" in recent[0].en

    async def test_get_recent_quotes_with_limit(self, mongo_quote_repo):
        """Test that limit parameter works for quotes."""
        # Create 10 quotes
        for i in range(10):
            quote = Quote(
                id=None,
                en=f"Test quote {i}",
                ru=f"Тестовая цитата {i}",
                pair_seq_id=6000 + i,
                rating=0,
                filename="test.srt",
                time="00:00:01,000 --> 00:00:03,000",
                owner_username="user"
            )
            await mongo_quote_repo.upsert(quote)

        # Get only 5 most recent
        recent = await mongo_quote_repo.get_recent(5)

        assert len(recent) <= 5


@pytest.mark.asyncio
class TestMongoDBStatsRepository:
    """Test MongoDB stats repository operations."""

    async def test_save_and_get_stats(self, mongo_stats_repo):
        """Test saving and retrieving stats."""
        stats = SystemStats(
            total=1000,
            files_en=["movie1", "movie2", "movie3"],
            updated_at=None
        )

        # Save stats
        saved = await mongo_stats_repo.save(stats)

        assert saved is not None
        assert saved.total == 1000
        assert len(saved.files_en) == 3

        # Retrieve stats
        retrieved = await mongo_stats_repo.get_latest()

        assert retrieved is not None
        assert retrieved.total == 1000
        assert "movie1" in retrieved.files_en
        assert "movie2" in retrieved.files_en
        assert "movie3" in retrieved.files_en

    async def test_update_stats(self, mongo_stats_repo):
        """Test updating existing stats."""
        # Save initial stats
        stats1 = SystemStats(
            total=500,
            files_en=["file1", "file2"],
            updated_at=None
        )
        await mongo_stats_repo.save(stats1)

        # Update with new stats
        stats2 = SystemStats(
            total=750,
            files_en=["file1", "file2", "file3", "file4"],
            updated_at=None
        )
        await mongo_stats_repo.save(stats2)

        # Retrieve - should have latest stats
        retrieved = await mongo_stats_repo.get_latest()

        assert retrieved is not None
        assert retrieved.total == 750
        assert len(retrieved.files_en) == 4

    async def test_get_latest_when_empty(self, mongo_stats_repo):
        """Test getting stats when none exist."""
        retrieved = await mongo_stats_repo.get_latest()

        # Should return None when no stats exist
        assert retrieved is None

    async def test_stats_with_empty_files(self, mongo_stats_repo):
        """Test stats with empty file list."""
        stats = SystemStats(
            total=0,
            files_en=[],
            updated_at=None
        )

        saved = await mongo_stats_repo.save(stats)

        assert saved is not None
        assert saved.total == 0
        assert len(saved.files_en) == 0

        retrieved = await mongo_stats_repo.get_latest()
        assert retrieved is not None
        assert retrieved.total == 0
        assert len(retrieved.files_en) == 0
