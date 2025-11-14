"""Tests for Subtitle API endpoints."""
import pytest
from httpx import AsyncClient
from src.domain.entities import SubtitlePair


@pytest.mark.asyncio
class TestSubtitleEndpoints:
    """Test subtitle API endpoints."""

    async def test_get_random_pair_success(
        self,
        async_client: AsyncClient,
        mongo_subtitle_repo
    ):
        """Test getting a random subtitle pair."""
        # Create some test pairs
        pairs = [
            SubtitlePair(
                id=None,
                en=f"Test subtitle {i}",
                ru=f"Тестовый субтитр {i}",
                file_en="test_en.srt",
                file_ru="test_ru.srt",
                time_en=f"00:00:{i:02d},000 --> 00:00:{i+2:02d},000",
                time_ru=f"00:00:{i:02d},000 --> 00:00:{i+2:02d},000",
                rating=0,
                category=None,
                seq_id=100 + i
            )
            for i in range(5)
        ]
        await mongo_subtitle_repo.create_many(pairs)

        # Get random pair
        response = await async_client.get("/api/get_random")

        assert response.status_code == 200
        data = response.json()

        assert "id" in data
        assert "en" in data
        assert "ru" in data
        assert "Test subtitle" in data["en"]

    async def test_get_random_pair_not_found(self, async_client: AsyncClient):
        """Test getting random pair when database is empty."""
        # Database is empty (cleaned by fixture)
        response = await async_client.get("/api/get_random")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    async def test_get_pair_by_id(
        self,
        async_client: AsyncClient,
        mongo_subtitle_repo
    ):
        """Test getting a specific pair by ID."""
        # Create a pair
        pair = SubtitlePair(
            id=None,
            en="Specific subtitle",
            ru="Конкретный субтитр",
            file_en="test_en.srt",
            file_ru="test_ru.srt",
            time_en="00:00:10,000 --> 00:00:12,000",
            time_ru="00:00:10,000 --> 00:00:12,000",
            rating=0,
            category=None,
            seq_id=200
        )
        created = await mongo_subtitle_repo.create(pair)

        # Get by ID
        response = await async_client.get(f"/api/search/{created.id}/")

        assert response.status_code == 200
        data = response.json()

        assert data["id"] == created.id
        assert data["en"] == "Specific subtitle"
        assert data["ru"] == "Конкретный субтитр"

    async def test_get_pair_by_id_with_offset(
        self,
        async_client: AsyncClient,
        mongo_subtitle_repo
    ):
        """Test temporal navigation with offset."""
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
                seq_id=300 + i
            )
            for i in range(5)
        ]
        created_pairs = []
        for p in pairs:
            created = await mongo_subtitle_repo.create(p)
            created_pairs.append(created)

        middle_pair = created_pairs[2]

        # Get with offset +1 (next)
        response = await async_client.get(
            f"/api/search/{middle_pair.id}/",
            params={"offset": 1}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["seq_id"] == 303

        # Get with offset -1 (previous)
        response = await async_client.get(
            f"/api/search/{middle_pair.id}/",
            params={"offset": -1}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["seq_id"] == 301

    async def test_get_pair_not_found(self, async_client: AsyncClient):
        """Test getting non-existent pair."""
        response = await async_client.get("/api/search/507f1f77bcf86cd799439011/")

        assert response.status_code == 404

    async def test_update_pair_rating_authenticated(
        self,
        authenticated_client: AsyncClient,
        mongo_subtitle_repo
    ):
        """Test updating pair rating (requires auth)."""
        # Create a pair
        pair = SubtitlePair(
            id=None,
            en="Rate this",
            ru="Оцени это",
            file_en="test_en.srt",
            file_ru="test_ru.srt",
            time_en="00:00:15,000 --> 00:00:17,000",
            time_ru="00:00:15,000 --> 00:00:17,000",
            rating=0,
            category=None,
            seq_id=400
        )
        created = await mongo_subtitle_repo.create(pair)

        # Update rating (+1)
        response = await authenticated_client.patch(
            f"/api/search/{created.id}/",
            params={"delta": 1}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["rating"] == 1

    async def test_update_pair_category_authenticated(
        self,
        authenticated_client: AsyncClient,
        mongo_subtitle_repo
    ):
        """Test updating pair category (requires auth)."""
        # Create a pair
        pair = SubtitlePair(
            id=None,
            en="Categorize this",
            ru="Категоризируй это",
            file_en="test_en.srt",
            file_ru="test_ru.srt",
            time_en="00:00:20,000 --> 00:00:22,000",
            time_ru="00:00:20,000 --> 00:00:22,000",
            rating=0,
            category=None,
            seq_id=500
        )
        created = await mongo_subtitle_repo.create(pair)

        # Set category to 'idiom'
        response = await authenticated_client.patch(
            f"/api/search/{created.id}/",
            params={"category": "idiom"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["category"] == "idiom"

    async def test_update_pair_unauthenticated(
        self,
        async_client: AsyncClient,
        mongo_subtitle_repo
    ):
        """Test that updating pair without auth fails."""
        # Create a pair
        pair = SubtitlePair(
            id=None,
            en="Cannot update",
            ru="Не может обновить",
            file_en="test_en.srt",
            file_ru="test_ru.srt",
            time_en="00:00:25,000 --> 00:00:27,000",
            time_ru="00:00:25,000 --> 00:00:27,000",
            rating=0,
            category=None,
            seq_id=600
        )
        created = await mongo_subtitle_repo.create(pair)

        # Try to update without auth
        response = await async_client.patch(
            f"/api/search/{created.id}/",
            params={"delta": 1}
        )

        assert response.status_code in [401, 403]

    async def test_search_pairs(
        self,
        async_client: AsyncClient,
        mongo_subtitle_repo
    ):
        """Test searching for subtitle pairs."""
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
                seq_id=701
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
                seq_id=702
            )
        ]
        await mongo_subtitle_repo.create_many(pairs)

        # Search for 'fox'
        response = await async_client.get("/api/search", params={"q": "fox"})

        assert response.status_code == 200
        data = response.json()

        assert isinstance(data, list)
        assert len(data) >= 1
        assert any("fox" in item["en"].lower() for item in data)

    async def test_search_pairs_exact_phrase(
        self,
        async_client: AsyncClient,
        mongo_subtitle_repo
    ):
        """Test searching with exact phrase."""
        # Create a pair
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
            seq_id=800
        )
        await mongo_subtitle_repo.create(pair)

        # Search with exact phrase
        response = await async_client.get("/api/search", params={"q": '"have a dream"'})

        assert response.status_code == 200
        data = response.json()

        assert len(data) >= 1
        assert any("have a dream" in item["en"].lower() for item in data)

    async def test_get_idioms(
        self,
        async_client: AsyncClient,
        mongo_idiom_repo
    ):
        """Test getting recent idioms."""
        from src.domain.entities import Idiom

        # Create test idioms
        idioms = [
            Idiom(
                id=None,
                en=f"Idiom {i}",
                ru=f"Идиома {i}",
                pair_seq_id=900 + i,
                rating=0,
                filename="test.srt",
                time="00:00:01,000 --> 00:00:03,000",
                owner_username="testuser"
            )
            for i in range(3)
        ]

        for idiom in idioms:
            await mongo_idiom_repo.upsert(idiom)

        # Get idioms
        response = await async_client.get("/api/idioms")

        assert response.status_code == 200
        data = response.json()

        assert isinstance(data, list)
        assert len(data) >= 3

    async def test_get_quotes(
        self,
        async_client: AsyncClient,
        mongo_quote_repo
    ):
        """Test getting recent quotes."""
        from src.domain.entities import Quote

        # Create test quotes
        quotes = [
            Quote(
                id=None,
                en=f"Quote {i}",
                ru=f"Цитата {i}",
                pair_seq_id=1000 + i,
                rating=0,
                filename="test.srt",
                time="00:00:01,000 --> 00:00:03,000",
                owner_username="testuser"
            )
            for i in range(3)
        ]

        for quote in quotes:
            await mongo_quote_repo.upsert(quote)

        # Get quotes
        response = await async_client.get("/api/quotes")

        assert response.status_code == 200
        data = response.json()

        assert isinstance(data, list)
        assert len(data) >= 3

    async def test_get_stats(
        self,
        async_client: AsyncClient,
        mongo_stats_repo
    ):
        """Test getting system statistics."""
        from src.domain.entities import SystemStats

        # Create stats
        stats = SystemStats(
            total=1500,
            files_en=["movie1", "movie2", "movie3"],
            updated_at=None
        )
        await mongo_stats_repo.save(stats)

        # Get stats
        response = await async_client.get("/api/stats")

        assert response.status_code == 200
        data = response.json()

        assert data["total"] == 1500
        assert len(data["files_en"]) == 3
        assert "movie1" in data["files_en"]

    async def test_compute_stats(
        self,
        async_client: AsyncClient,
        mongo_subtitle_repo
    ):
        """Test computing statistics."""
        # Create some pairs
        pairs = [
            SubtitlePair(
                id=None,
                en=f"Stats test {i}",
                ru=f"Тест статистики {i}",
                file_en=f"file{i}_en.srt",
                file_ru=f"file{i}_ru.srt",
                time_en="00:00:01,000 --> 00:00:03,000",
                time_ru="00:00:01,000 --> 00:00:03,000",
                rating=0,
                category=None,
                seq_id=1100 + i
            )
            for i in range(5)
        ]
        await mongo_subtitle_repo.create_many(pairs)

        # Compute stats
        response = await async_client.post("/api/stats")

        assert response.status_code == 200
        data = response.json()

        assert data["total"] >= 5
        assert len(data["files_en"]) >= 5

    async def test_clear_duplicates(
        self,
        async_client: AsyncClient,
        mongo_subtitle_repo
    ):
        """Test clearing duplicate pairs."""
        # Create duplicate pairs
        duplicate_en = "Duplicate text"
        duplicate_ru = "Дублированный текст"

        pairs = [
            SubtitlePair(
                id=None,
                en=duplicate_en,
                ru=duplicate_ru,
                file_en=f"file{i}_en.srt",
                file_ru=f"file{i}_ru.srt",
                time_en="00:00:01,000 --> 00:00:03,000",
                time_ru="00:00:01,000 --> 00:00:03,000",
                rating=0,
                category=None,
                seq_id=1200 + i
            )
            for i in range(3)
        ]
        await mongo_subtitle_repo.create_many(pairs)

        # Clear duplicates
        response = await async_client.post("/api/clear")

        assert response.status_code == 200
        data = response.json()

        # Should have deleted 2 (kept 1)
        assert data["deleted_count"] == 2

    async def test_delete_all_pairs(
        self,
        async_client: AsyncClient,
        mongo_subtitle_repo
    ):
        """Test deleting all pairs."""
        # Create some pairs
        pairs = [
            SubtitlePair(
                id=None,
                en=f"Delete me {i}",
                ru=f"Удали меня {i}",
                file_en="test_en.srt",
                file_ru="test_ru.srt",
                time_en="00:00:01,000 --> 00:00:03,000",
                time_ru="00:00:01,000 --> 00:00:03,000",
                rating=0,
                category=None,
                seq_id=1300 + i
            )
            for i in range(5)
        ]
        await mongo_subtitle_repo.create_many(pairs)

        # Delete all
        response = await async_client.post("/api/delete_all")

        assert response.status_code == 200
        data = response.json()

        assert data["deleted_count"] >= 5

        # Verify all deleted
        count = await mongo_subtitle_repo.count_total()
        assert count == 0
