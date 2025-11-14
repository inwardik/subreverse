"""Tests for MongoDB Subtitle Pair Repository."""
import pytest
from src.domain.entities import SubtitlePair


@pytest.mark.asyncio
class TestMongoDBSubtitlePairRepository:
    """Test MongoDB subtitle pair repository operations."""

    async def test_create_pair(self, mongo_subtitle_repo):
        """Test creating a subtitle pair."""
        pair = SubtitlePair(
            id=None,
            en="Hello, world!",
            ru="Привет, мир!",
            file_en="test_en.srt",
            file_ru="test_ru.srt",
            time_en="00:00:01,000 --> 00:00:03,000",
            time_ru="00:00:01,000 --> 00:00:03,000",
            rating=0,
            category=None,
            seq_id=1
        )

        created = await mongo_subtitle_repo.create(pair)

        assert created is not None
        assert created.id is not None
        assert created.en == "Hello, world!"
        assert created.ru == "Привет, мир!"
        assert created.seq_id == 1

    async def test_get_by_id(self, mongo_subtitle_repo):
        """Test retrieving pair by ID."""
        # Create pair
        pair = SubtitlePair(
            id=None,
            en="Good morning",
            ru="Доброе утро",
            file_en="test_en.srt",
            file_ru="test_ru.srt",
            time_en="00:00:05,000 --> 00:00:07,000",
            time_ru="00:00:05,000 --> 00:00:07,000",
            rating=0,
            category=None,
            seq_id=2
        )
        created = await mongo_subtitle_repo.create(pair)

        # Retrieve pair
        retrieved = await mongo_subtitle_repo.get_by_id(created.id)

        assert retrieved is not None
        assert retrieved.id == created.id
        assert retrieved.en == "Good morning"
        assert retrieved.ru == "Доброе утро"

    async def test_get_by_seq_id(self, mongo_subtitle_repo):
        """Test retrieving pair by seq_id."""
        # Create pair
        pair = SubtitlePair(
            id=None,
            en="Thank you",
            ru="Спасибо",
            file_en="test_en.srt",
            file_ru="test_ru.srt",
            time_en="00:00:10,000 --> 00:00:12,000",
            time_ru="00:00:10,000 --> 00:00:12,000",
            rating=0,
            category=None,
            seq_id=100
        )
        await mongo_subtitle_repo.create(pair)

        # Retrieve by seq_id
        retrieved = await mongo_subtitle_repo.get_by_seq_id(100)

        assert retrieved is not None
        assert retrieved.seq_id == 100
        assert retrieved.en == "Thank you"

    async def test_create_many(self, mongo_subtitle_repo):
        """Test creating multiple pairs at once."""
        pairs = [
            SubtitlePair(
                id=None,
                en=f"Subtitle {i}",
                ru=f"Субтитр {i}",
                file_en="test_en.srt",
                file_ru="test_ru.srt",
                time_en=f"00:00:{i:02d},000 --> 00:00:{i+2:02d},000",
                time_ru=f"00:00:{i:02d},000 --> 00:00:{i+2:02d},000",
                rating=0,
                category=None,
                seq_id=1000 + i
            )
            for i in range(5)
        ]

        count = await mongo_subtitle_repo.create_many(pairs)

        assert count == 5

        # Verify they were created
        total = await mongo_subtitle_repo.count_total()
        assert total >= 5

    async def test_update_rating(self, mongo_subtitle_repo):
        """Test updating pair rating."""
        # Create pair
        pair = SubtitlePair(
            id=None,
            en="Nice phrase",
            ru="Хорошая фраза",
            file_en="test_en.srt",
            file_ru="test_ru.srt",
            time_en="00:00:15,000 --> 00:00:17,000",
            time_ru="00:00:15,000 --> 00:00:17,000",
            rating=0,
            category=None,
            seq_id=200
        )
        created = await mongo_subtitle_repo.create(pair)

        # Update rating (+1)
        updated = await mongo_subtitle_repo.update_rating(created.id, 1)

        assert updated is not None
        assert updated.rating == 1

        # Update rating again (+2)
        updated = await mongo_subtitle_repo.update_rating(created.id, 2)
        assert updated.rating == 3

        # Decrease rating (-1)
        updated = await mongo_subtitle_repo.update_rating(created.id, -1)
        assert updated.rating == 2

    async def test_update_category(self, mongo_subtitle_repo):
        """Test updating pair category."""
        # Create pair
        pair = SubtitlePair(
            id=None,
            en="Break a leg!",
            ru="Ни пуха, ни пера!",
            file_en="test_en.srt",
            file_ru="test_ru.srt",
            time_en="00:00:20,000 --> 00:00:22,000",
            time_ru="00:00:20,000 --> 00:00:22,000",
            rating=0,
            category=None,
            seq_id=300
        )
        created = await mongo_subtitle_repo.create(pair)

        # Set category to 'idiom'
        updated = await mongo_subtitle_repo.update_category(created.id, "idiom")

        assert updated is not None
        assert updated.category == "idiom"

        # Change category to 'quote'
        updated = await mongo_subtitle_repo.update_category(created.id, "quote")
        assert updated.category == "quote"

        # Unset category (None)
        updated = await mongo_subtitle_repo.update_category(created.id, None)
        assert updated.category is None

    async def test_delete_pair(self, mongo_subtitle_repo):
        """Test deleting a pair."""
        # Create pair
        pair = SubtitlePair(
            id=None,
            en="To be deleted",
            ru="Быть удалённым",
            file_en="test_en.srt",
            file_ru="test_ru.srt",
            time_en="00:00:25,000 --> 00:00:27,000",
            time_ru="00:00:25,000 --> 00:00:27,000",
            rating=0,
            category=None,
            seq_id=400
        )
        created = await mongo_subtitle_repo.create(pair)

        # Delete pair
        success = await mongo_subtitle_repo.delete(created.id)
        assert success is True

        # Verify it's deleted
        retrieved = await mongo_subtitle_repo.get_by_id(created.id)
        assert retrieved is None

    async def test_search_simple(self, mongo_subtitle_repo):
        """Test searching for pairs."""
        # Create test pairs
        pairs = [
            SubtitlePair(
                id=None,
                en="The quick brown fox",
                ru="Быстрая коричневая лиса",
                file_en="test_en.srt",
                file_ru="test_ru.srt",
                time_en="00:00:01,000 --> 00:00:03,000",
                time_ru="00:00:01,000 --> 00:00:03,000",
                rating=0,
                category=None,
                seq_id=501
            ),
            SubtitlePair(
                id=None,
                en="The lazy dog",
                ru="Ленивая собака",
                file_en="test_en.srt",
                file_ru="test_ru.srt",
                time_en="00:00:05,000 --> 00:00:07,000",
                time_ru="00:00:05,000 --> 00:00:07,000",
                rating=0,
                category=None,
                seq_id=502
            )
        ]
        await mongo_subtitle_repo.create_many(pairs)

        # Search for 'fox'
        results = await mongo_subtitle_repo.search("fox")

        assert len(results) >= 1
        assert any("fox" in r.en.lower() for r in results)

        # Search for 'собака' (Russian)
        results = await mongo_subtitle_repo.search("собака")
        assert len(results) >= 1
        assert any("собака" in r.ru.lower() for r in results)

    async def test_search_exact_phrase(self, mongo_subtitle_repo):
        """Test searching with exact phrase (quoted)."""
        # Create test pairs
        pair = SubtitlePair(
            id=None,
            en="I have a dream",
            ru="У меня есть мечта",
            file_en="test_en.srt",
            file_ru="test_ru.srt",
            time_en="00:00:01,000 --> 00:00:03,000",
            time_ru="00:00:01,000 --> 00:00:03,000",
            rating=0,
            category=None,
            seq_id=600
        )
        await mongo_subtitle_repo.create(pair)

        # Search with exact phrase
        results = await mongo_subtitle_repo.search('"have a dream"')

        assert len(results) >= 1
        assert any("have a dream" in r.en.lower() for r in results)

    async def test_get_random(self, mongo_subtitle_repo):
        """Test getting a random pair."""
        # Create multiple pairs
        pairs = [
            SubtitlePair(
                id=None,
                en=f"Random subtitle {i}",
                ru=f"Случайный субтитр {i}",
                file_en="test_en.srt",
                file_ru="test_ru.srt",
                time_en=f"00:00:{i:02d},000 --> 00:00:{i+2:02d},000",
                time_ru=f"00:00:{i:02d},000 --> 00:00:{i+2:02d},000",
                rating=0,
                category=None,
                seq_id=700 + i
            )
            for i in range(10)
        ]
        await mongo_subtitle_repo.create_many(pairs)

        # Get random pair
        random_pair = await mongo_subtitle_repo.get_random()

        assert random_pair is not None
        assert random_pair.en.startswith("Random subtitle")

    async def test_count_total(self, mongo_subtitle_repo):
        """Test counting total pairs."""
        # Initially 0
        count = await mongo_subtitle_repo.count_total()
        initial_count = count

        # Add some pairs
        pairs = [
            SubtitlePair(
                id=None,
                en=f"Count test {i}",
                ru=f"Тест подсчёта {i}",
                file_en="test_en.srt",
                file_ru="test_ru.srt",
                time_en=f"00:00:{i:02d},000 --> 00:00:{i+2:02d},000",
                time_ru=f"00:00:{i:02d},000 --> 00:00:{i+2:02d},000",
                rating=0,
                category=None,
                seq_id=800 + i
            )
            for i in range(3)
        ]
        await mongo_subtitle_repo.create_many(pairs)

        # Count should increase
        count = await mongo_subtitle_repo.count_total()
        assert count == initial_count + 3

    async def test_clear_duplicates(self, mongo_subtitle_repo):
        """Test removing duplicate pairs."""
        # Create duplicate pairs
        duplicate_text_en = "Duplicate subtitle"
        duplicate_text_ru = "Дублированный субтитр"

        pairs = [
            SubtitlePair(
                id=None,
                en=duplicate_text_en,
                ru=duplicate_text_ru,
                file_en="test1_en.srt",
                file_ru="test1_ru.srt",
                time_en="00:00:01,000 --> 00:00:03,000",
                time_ru="00:00:01,000 --> 00:00:03,000",
                rating=0,
                category=None,
                seq_id=900 + i
            )
            for i in range(3)  # Create 3 identical pairs
        ]
        await mongo_subtitle_repo.create_many(pairs)

        # Clear duplicates
        deleted_count = await mongo_subtitle_repo.clear_duplicates()

        # Should have deleted 2 (kept 1)
        assert deleted_count == 2

        # Verify only 1 remains
        results = await mongo_subtitle_repo.search(duplicate_text_en)
        assert len(results) == 1

    async def test_get_distinct_files_en(self, mongo_subtitle_repo):
        """Test getting distinct file list."""
        # Create pairs from different files
        files = ["movie1_en.srt", "movie2_en.srt", "movie3_en.srt"]
        for i, file in enumerate(files):
            pair = SubtitlePair(
                id=None,
                en=f"Subtitle from {file}",
                ru=f"Субтитр из {file}",
                file_en=file,
                file_ru=file.replace("_en", "_ru"),
                time_en="00:00:01,000 --> 00:00:03,000",
                time_ru="00:00:01,000 --> 00:00:03,000",
                rating=0,
                category=None,
                seq_id=1000 + i
            )
            await mongo_subtitle_repo.create(pair)

        # Get distinct files
        distinct_files = await mongo_subtitle_repo.get_distinct_files_en()

        # Should contain the file names without _en.srt suffix
        assert len(distinct_files) >= 3
        assert "movie1" in distinct_files
        assert "movie2" in distinct_files
        assert "movie3" in distinct_files

    async def test_get_neighbor_offset_zero(self, mongo_subtitle_repo):
        """Test getting neighbor with offset 0 returns same pair."""
        # Create pair
        pair = SubtitlePair(
            id=None,
            en="Original subtitle",
            ru="Оригинальный субтитр",
            file_en="test_en.srt",
            file_ru="test_ru.srt",
            time_en="00:00:10,000 --> 00:00:12,000",
            time_ru="00:00:10,000 --> 00:00:12,000",
            rating=0,
            category=None,
            seq_id=1100
        )
        created = await mongo_subtitle_repo.create(pair)

        # Get neighbor with offset 0
        neighbor = await mongo_subtitle_repo.get_neighbor(created.id, 0)

        assert neighbor is not None
        assert neighbor.id == created.id
        assert neighbor.en == "Original subtitle"

    async def test_get_neighbor_with_seq_id(self, mongo_subtitle_repo):
        """Test temporal navigation using seq_id."""
        # Create sequence of pairs
        pairs = [
            SubtitlePair(
                id=None,
                en=f"Sequence {i}",
                ru=f"Последовательность {i}",
                file_en="sequence_en.srt",
                file_ru="sequence_ru.srt",
                time_en=f"00:00:{i*5:02d},000 --> 00:00:{i*5+3:02d},000",
                time_ru=f"00:00:{i*5:02d},000 --> 00:00:{i*5+3:02d},000",
                rating=0,
                category=None,
                seq_id=1200 + i
            )
            for i in range(5)
        ]
        created_pairs = []
        for p in pairs:
            created = await mongo_subtitle_repo.create(p)
            created_pairs.append(created)

        # Get middle pair
        middle_pair = created_pairs[2]

        # Get next pair (offset +1)
        next_pair = await mongo_subtitle_repo.get_neighbor(middle_pair.id, 1)
        assert next_pair is not None
        assert next_pair.seq_id == 1203

        # Get previous pair (offset -1)
        prev_pair = await mongo_subtitle_repo.get_neighbor(middle_pair.id, -1)
        assert prev_pair is not None
        assert prev_pair.seq_id == 1201
