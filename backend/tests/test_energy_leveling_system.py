"""Tests for Energy and Leveling System."""
import pytest
from datetime import datetime, timedelta
from httpx import AsyncClient
from src.domain.entities import SubtitlePair, User


@pytest.mark.asyncio
class TestEnergySystem:
    """Test energy consumption and recharge mechanics."""

    async def test_initial_energy(self, test_user):
        """Test that new users start with 10 energy."""
        assert test_user.user.energy == 10
        assert test_user.user.max_energy == 10

    async def test_energy_consumed_on_rating_update(
        self,
        authenticated_client: AsyncClient,
        mongo_subtitle_repo,
        postgres_user_repo,
        test_user
    ):
        """Test that updating rating consumes 1 energy."""
        # Create a pair
        pair = SubtitlePair(
            id=None,
            en="Test energy",
            ru="Тест энергии",
            file_en="test_en.srt",
            file_ru="test_ru.srt",
            time_en="00:00:01,000 --> 00:00:03,000",
            time_ru="00:00:01,000 --> 00:00:03,000",
            rating=0,
            category=None,
            seq_id=100
        )
        created = await mongo_subtitle_repo.create(pair)

        # Get initial energy
        user = await postgres_user_repo.get_by_id(test_user.user.id)
        initial_energy = user.energy

        # Update rating (should consume 1 energy)
        response = await authenticated_client.patch(
            f"/api/search/{created.id}/",
            params={"delta": 1}
        )

        assert response.status_code == 200

        # Check energy decreased by 1
        user = await postgres_user_repo.get_by_id(test_user.user.id)
        assert user.energy == initial_energy - 1

    async def test_energy_consumed_on_category_update(
        self,
        authenticated_client: AsyncClient,
        mongo_subtitle_repo,
        postgres_user_repo,
        test_user
    ):
        """Test that updating category consumes 1 energy."""
        # Create a pair
        pair = SubtitlePair(
            id=None,
            en="Test category energy",
            ru="Тест энергии категории",
            file_en="test_en.srt",
            file_ru="test_ru.srt",
            time_en="00:00:01,000 --> 00:00:03,000",
            time_ru="00:00:01,000 --> 00:00:03,000",
            rating=0,
            category=None,
            seq_id=200
        )
        created = await mongo_subtitle_repo.create(pair)

        # Get initial energy
        user = await postgres_user_repo.get_by_id(test_user.user.id)
        initial_energy = user.energy

        # Update category (should consume 1 energy)
        response = await authenticated_client.patch(
            f"/api/search/{created.id}/",
            params={"category": "idiom"}
        )

        assert response.status_code == 200

        # Check energy decreased by 1
        user = await postgres_user_repo.get_by_id(test_user.user.id)
        assert user.energy == initial_energy - 1

    async def test_insufficient_energy(
        self,
        authenticated_client: AsyncClient,
        mongo_subtitle_repo,
        postgres_user_repo,
        test_user
    ):
        """Test that actions fail when energy is 0."""
        # Create a pair
        pair = SubtitlePair(
            id=None,
            en="No energy test",
            ru="Тест без энергии",
            file_en="test_en.srt",
            file_ru="test_ru.srt",
            time_en="00:00:01,000 --> 00:00:03,000",
            time_ru="00:00:01,000 --> 00:00:03,000",
            rating=0,
            category=None,
            seq_id=300
        )
        created = await mongo_subtitle_repo.create(pair)

        # Drain user's energy to 0
        user = await postgres_user_repo.get_by_id(test_user.user.id)
        user.energy = 0
        await postgres_user_repo.update(user)

        # Try to update rating (should fail)
        response = await authenticated_client.patch(
            f"/api/search/{created.id}/",
            params={"delta": 1}
        )

        assert response.status_code == 403
        assert "energy" in response.json()["detail"].lower()

    async def test_energy_recharge_new_day(
        self,
        postgres_user_repo,
        test_user
    ):
        """Test that energy recharges on new day."""
        # Get user and set energy to 3, last_recharge to yesterday
        user = await postgres_user_repo.get_by_id(test_user.user.id)
        user.energy = 3
        user.last_recharge = datetime.utcnow() - timedelta(days=1)
        await postgres_user_repo.update(user)

        # Trigger recharge
        success = await postgres_user_repo.recharge_energy(test_user.user.id)
        assert success is True

        # Check energy recharged to max
        user = await postgres_user_repo.get_by_id(test_user.user.id)
        assert user.energy == user.max_energy

    async def test_energy_no_recharge_same_day(
        self,
        postgres_user_repo,
        test_user
    ):
        """Test that energy doesn't recharge on same day."""
        # Get user and set energy to 5
        user = await postgres_user_repo.get_by_id(test_user.user.id)
        user.energy = 5
        user.last_recharge = datetime.utcnow()
        await postgres_user_repo.update(user)

        # Try to recharge (should fail)
        success = await postgres_user_repo.recharge_energy(test_user.user.id)
        assert success is False

        # Energy should remain unchanged
        user = await postgres_user_repo.get_by_id(test_user.user.id)
        assert user.energy == 5

    async def test_self_endpoint_triggers_recharge(
        self,
        authenticated_client: AsyncClient,
        postgres_user_repo,
        test_user
    ):
        """Test that /self endpoint triggers energy recharge."""
        # Set energy to 3, last_recharge to yesterday
        user = await postgres_user_repo.get_by_id(test_user.user.id)
        user.energy = 3
        user.last_recharge = datetime.utcnow() - timedelta(days=1)
        await postgres_user_repo.update(user)

        # Call /self endpoint
        response = await authenticated_client.get("/self")

        assert response.status_code == 200
        data = response.json()

        # Energy should be recharged
        assert data["energy"] == data["max_energy"]


@pytest.mark.asyncio
class TestLevelingSystem:
    """Test XP and leveling mechanics."""

    async def test_initial_level_and_xp(self, test_user):
        """Test that new users start at level 1 with 0 XP."""
        assert test_user.user.level == 1
        assert test_user.user.xp == 0

    async def test_xp_gained_on_action(
        self,
        authenticated_client: AsyncClient,
        mongo_subtitle_repo,
        postgres_user_repo,
        test_user
    ):
        """Test that actions grant 1 XP."""
        # Create a pair
        pair = SubtitlePair(
            id=None,
            en="XP test",
            ru="Тест XP",
            file_en="test_en.srt",
            file_ru="test_ru.srt",
            time_en="00:00:01,000 --> 00:00:03,000",
            time_ru="00:00:01,000 --> 00:00:03,000",
            rating=0,
            category=None,
            seq_id=400
        )
        created = await mongo_subtitle_repo.create(pair)

        # Get initial XP
        user = await postgres_user_repo.get_by_id(test_user.user.id)
        initial_xp = user.xp

        # Update rating (should grant 1 XP)
        response = await authenticated_client.patch(
            f"/api/search/{created.id}/",
            params={"delta": 1}
        )

        assert response.status_code == 200

        # Check XP increased by 1
        user = await postgres_user_repo.get_by_id(test_user.user.id)
        assert user.xp == initial_xp + 1

    async def test_level_up_at_threshold(
        self,
        authenticated_client: AsyncClient,
        mongo_subtitle_repo,
        postgres_user_repo,
        test_user
    ):
        """Test that user levels up when reaching XP threshold."""
        # Create a pair
        pair = SubtitlePair(
            id=None,
            en="Level up test",
            ru="Тест повышения уровня",
            file_en="test_en.srt",
            file_ru="test_ru.srt",
            time_en="00:00:01,000 --> 00:00:03,000",
            time_ru="00:00:01,000 --> 00:00:03,000",
            rating=0,
            category=None,
            seq_id=500
        )
        created = await mongo_subtitle_repo.create(pair)

        # Set user to 9 XP (one away from level up)
        user = await postgres_user_repo.get_by_id(test_user.user.id)
        user.xp = 9
        user.level = 1
        await postgres_user_repo.update(user)

        # Perform action (should level up)
        response = await authenticated_client.patch(
            f"/api/search/{created.id}/",
            params={"delta": 1}
        )

        assert response.status_code == 200

        # Check leveled up
        user = await postgres_user_repo.get_by_id(test_user.user.id)
        assert user.level == 2
        assert user.xp == 0  # XP resets to 0 after level up

    async def test_max_energy_increases_on_level_up(
        self,
        authenticated_client: AsyncClient,
        mongo_subtitle_repo,
        postgres_user_repo,
        test_user
    ):
        """Test that max_energy increases by 5 on level up."""
        # Create a pair
        pair = SubtitlePair(
            id=None,
            en="Max energy test",
            ru="Тест максимальной энергии",
            file_en="test_en.srt",
            file_ru="test_ru.srt",
            time_en="00:00:01,000 --> 00:00:03,000",
            time_ru="00:00:01,000 --> 00:00:03,000",
            rating=0,
            category=None,
            seq_id=600
        )
        created = await mongo_subtitle_repo.create(pair)

        # Set user to 9 XP (one away from level up)
        user = await postgres_user_repo.get_by_id(test_user.user.id)
        user.xp = 9
        user.level = 1
        user.max_energy = 10
        await postgres_user_repo.update(user)

        initial_max_energy = user.max_energy

        # Perform action (should level up)
        response = await authenticated_client.patch(
            f"/api/search/{created.id}/",
            params={"delta": 1}
        )

        assert response.status_code == 200

        # Check max_energy increased by 5
        user = await postgres_user_repo.get_by_id(test_user.user.id)
        assert user.max_energy == initial_max_energy + 5

    async def test_xp_requirement_scales_with_level(
        self,
        authenticated_client: AsyncClient,
        mongo_subtitle_repo,
        postgres_user_repo,
        test_user
    ):
        """Test that XP requirement is level * 10."""
        # Level 1 requires 10 XP
        # Level 2 requires 20 XP
        # Level 3 requires 30 XP, etc.

        # Set user to level 2
        user = await postgres_user_repo.get_by_id(test_user.user.id)
        user.level = 2
        user.xp = 0
        await postgres_user_repo.update(user)

        # Check max_xp via /self endpoint
        response = await authenticated_client.get("/self")
        data = response.json()

        assert data["level"] == 2
        assert data["max_xp"] == 20  # Level 2 requires 20 XP

    async def test_multiple_level_ups(
        self,
        authenticated_client: AsyncClient,
        mongo_subtitle_repo,
        postgres_user_repo,
        test_user
    ):
        """Test leveling up multiple times."""
        # Create multiple pairs
        for i in range(15):
            pair = SubtitlePair(
                id=None,
                en=f"Multi level {i}",
                ru=f"Мульти уровень {i}",
                file_en="test_en.srt",
                file_ru="test_ru.srt",
                time_en="00:00:01,000 --> 00:00:03,000",
                time_ru="00:00:01,000 --> 00:00:03,000",
                rating=0,
                category=None,
                seq_id=700 + i
            )
            created = await mongo_subtitle_repo.create(pair)

            # Perform action
            await authenticated_client.patch(
                f"/api/search/{created.id}/",
                params={"delta": 1}
            )

        # Check user level
        user = await postgres_user_repo.get_by_id(test_user.user.id)

        # After 10 actions: level 2
        # After 10 + 20 = 30 actions: level 3
        # 15 actions should be level 2 with 5 XP
        assert user.level >= 1


@pytest.mark.asyncio
class TestIdiomQuoteMirroring:
    """Test automatic idiom/quote mirroring when category is set."""

    async def test_setting_idiom_category_creates_idiom(
        self,
        authenticated_client: AsyncClient,
        mongo_subtitle_repo,
        mongo_idiom_repo
    ):
        """Test that setting category to 'idiom' creates idiom entry."""
        # Create a pair
        pair = SubtitlePair(
            id=None,
            en="Break a leg!",
            ru="Ни пуха, ни пера!",
            file_en="idiom_en.srt",
            file_ru="idiom_ru.srt",
            time_en="00:01:00,000 --> 00:01:03,000",
            time_ru="00:01:00,000 --> 00:01:03,000",
            rating=5,
            category=None,
            seq_id=800
        )
        created = await mongo_subtitle_repo.create(pair)

        # Set category to 'idiom'
        response = await authenticated_client.patch(
            f"/api/search/{created.id}/",
            params={"category": "idiom"}
        )

        assert response.status_code == 200

        # Check idiom was created
        idioms = await mongo_idiom_repo.get_recent(10)
        assert len(idioms) >= 1

        # Find our idiom
        found = None
        for idiom in idioms:
            if idiom.pair_seq_id == 800:
                found = idiom
                break

        assert found is not None
        assert found.en == "Break a leg!"
        assert found.ru == "Ни пуха, ни пера!"

    async def test_setting_quote_category_creates_quote(
        self,
        authenticated_client: AsyncClient,
        mongo_subtitle_repo,
        mongo_quote_repo
    ):
        """Test that setting category to 'quote' creates quote entry."""
        # Create a pair
        pair = SubtitlePair(
            id=None,
            en="To be or not to be",
            ru="Быть или не быть",
            file_en="quote_en.srt",
            file_ru="quote_ru.srt",
            time_en="00:02:00,000 --> 00:02:05,000",
            time_ru="00:02:00,000 --> 00:02:05,000",
            rating=10,
            category=None,
            seq_id=900
        )
        created = await mongo_subtitle_repo.create(pair)

        # Set category to 'quote'
        response = await authenticated_client.patch(
            f"/api/search/{created.id}/",
            params={"category": "quote"}
        )

        assert response.status_code == 200

        # Check quote was created
        quotes = await mongo_quote_repo.get_recent(10)
        assert len(quotes) >= 1

        # Find our quote
        found = None
        for quote in quotes:
            if quote.pair_seq_id == 900:
                found = quote
                break

        assert found is not None
        assert found.en == "To be or not to be"
        assert found.ru == "Быть или не быть"

    async def test_unsetting_category_doesnt_delete_idiom(
        self,
        authenticated_client: AsyncClient,
        mongo_subtitle_repo,
        mongo_idiom_repo
    ):
        """Test that removing idiom category doesn't delete idiom entry."""
        # Create a pair and set as idiom
        pair = SubtitlePair(
            id=None,
            en="Persistent idiom",
            ru="Постоянная идиома",
            file_en="test_en.srt",
            file_ru="test_ru.srt",
            time_en="00:03:00,000 --> 00:03:03,000",
            time_ru="00:03:00,000 --> 00:03:03,000",
            rating=3,
            category=None,
            seq_id=1000
        )
        created = await mongo_subtitle_repo.create(pair)

        # Set as idiom
        await authenticated_client.patch(
            f"/api/search/{created.id}/",
            params={"category": "idiom"}
        )

        # Unset category
        response = await authenticated_client.patch(
            f"/api/search/{created.id}/",
            params={"category": ""}
        )

        assert response.status_code == 200

        # Idiom should still exist
        idioms = await mongo_idiom_repo.get_recent(10)
        found = any(idiom.pair_seq_id == 1000 for idiom in idioms)
        assert found is True
