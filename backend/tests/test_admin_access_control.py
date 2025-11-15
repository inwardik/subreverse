"""Tests for admin access control on protected endpoints."""
import pytest
import pytest_asyncio
from httpx import AsyncClient
from src.application.dto import SignupDTO


@pytest_asyncio.fixture
async def admin_user(auth_service, postgres_user_repo):
    """Create a test admin user."""
    # Create admin user
    signup_data = SignupDTO(
        username="adminuser",
        email="admin@example.com",
        password="adminpassword123"
    )
    result = await auth_service.signup(signup_data)

    # Update user role to admin
    user = await postgres_user_repo.get_by_username("adminuser")
    user.role = "admin"
    await postgres_user_repo.update(user)

    return result


@pytest_asyncio.fixture
async def admin_token(admin_user):
    """Get admin user token."""
    return admin_user.token


@pytest_asyncio.fixture
async def admin_client(async_client, admin_token) -> AsyncClient:
    """Create authenticated HTTP client with admin user."""
    async_client.headers.update({"Authorization": f"Bearer {admin_token}"})
    return async_client


@pytest_asyncio.fixture
async def regular_user(auth_service):
    """Create a regular (non-admin) test user."""
    signup_data = SignupDTO(
        username="regularuser",
        email="regular@example.com",
        password="regularpassword123"
    )
    result = await auth_service.signup(signup_data)
    return result


@pytest_asyncio.fixture
async def regular_user_token(regular_user):
    """Get regular user token."""
    return regular_user.token


@pytest_asyncio.fixture
async def regular_client(async_client, regular_user_token) -> AsyncClient:
    """Create authenticated HTTP client with regular user."""
    # Create a new client instance to avoid header conflicts
    from src.api.main import app
    async with AsyncClient(app=app, base_url="http://test") as client:
        client.headers.update({"Authorization": f"Bearer {regular_user_token}"})
        yield client


class TestAdminEndpointsAuthentication:
    """Test that admin endpoints require authentication."""

    @pytest.mark.asyncio
    async def test_upload_file_requires_auth(self, async_client):
        """Test that /api/upload_file requires authentication."""
        response = await async_client.post("/api/upload_file")
        assert response.status_code == 401
        assert "not authenticated" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_upload_zip_requires_auth(self, async_client):
        """Test that /api/upload_zip requires authentication."""
        response = await async_client.post("/api/upload_zip")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_import_ndjson_requires_auth(self, async_client):
        """Test that /api/import_ndjson requires authentication."""
        response = await async_client.post("/api/import_ndjson")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_export_requires_auth(self, async_client):
        """Test that /api/export requires authentication."""
        response = await async_client.post("/api/export")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_delete_all_requires_auth(self, async_client):
        """Test that /api/delete_all requires authentication."""
        response = await async_client.post("/api/delete_all")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_clear_requires_auth(self, async_client):
        """Test that /api/clear requires authentication."""
        response = await async_client.post("/api/clear")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_compute_stats_requires_auth(self, async_client):
        """Test that POST /api/stats requires authentication."""
        response = await async_client.post("/api/stats")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_reindex_elastic_requires_auth(self, async_client):
        """Test that /api/index_elastic_search requires authentication."""
        response = await async_client.post("/api/index_elastic_search")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_index_db_requires_auth(self, async_client):
        """Test that /api/index_db requires authentication."""
        response = await async_client.post("/api/index_db")
        assert response.status_code == 401


class TestAdminEndpointsAuthorization:
    """Test that admin endpoints reject non-admin users."""

    @pytest.mark.asyncio
    async def test_upload_file_rejects_non_admin(self, regular_client):
        """Test that /api/upload_file rejects non-admin users."""
        response = await regular_client.post("/api/upload_file")
        assert response.status_code == 403
        assert "admin" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_upload_zip_rejects_non_admin(self, regular_client):
        """Test that /api/upload_zip rejects non-admin users."""
        # Need to send a file, but it should fail before processing
        files = {"file": ("test.zip", b"fake content", "application/zip")}
        response = await regular_client.post("/api/upload_zip", files=files)
        assert response.status_code == 403
        assert "admin" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_import_ndjson_rejects_non_admin(self, regular_client):
        """Test that /api/import_ndjson rejects non-admin users."""
        files = {"file": ("test.ndjson", b"{}", "application/x-ndjson")}
        response = await regular_client.post("/api/import_ndjson", files=files)
        assert response.status_code == 403
        assert "admin" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_export_rejects_non_admin(self, regular_client):
        """Test that /api/export rejects non-admin users."""
        response = await regular_client.post("/api/export")
        assert response.status_code == 403
        assert "admin" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_delete_all_rejects_non_admin(self, regular_client):
        """Test that /api/delete_all rejects non-admin users."""
        response = await regular_client.post("/api/delete_all")
        assert response.status_code == 403
        assert "admin" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_clear_rejects_non_admin(self, regular_client):
        """Test that /api/clear rejects non-admin users."""
        response = await regular_client.post("/api/clear")
        assert response.status_code == 403
        assert "admin" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_compute_stats_rejects_non_admin(self, regular_client):
        """Test that POST /api/stats rejects non-admin users."""
        response = await regular_client.post("/api/stats")
        assert response.status_code == 403
        assert "admin" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_reindex_elastic_rejects_non_admin(self, regular_client):
        """Test that /api/index_elastic_search rejects non-admin users."""
        response = await regular_client.post("/api/index_elastic_search")
        assert response.status_code == 403
        assert "admin" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_index_db_rejects_non_admin(self, regular_client):
        """Test that /api/index_db rejects non-admin users."""
        response = await regular_client.post("/api/index_db")
        assert response.status_code == 403
        assert "admin" in response.json()["detail"].lower()


class TestAdminEndpointsAccess:
    """Test that admin endpoints allow admin users."""

    @pytest.mark.asyncio
    async def test_export_allows_admin(self, admin_client):
        """Test that /api/export allows admin users."""
        response = await admin_client.post("/api/export")
        # Should succeed (200) or fail with a different error (not 401/403)
        assert response.status_code not in [401, 403]

    @pytest.mark.asyncio
    async def test_delete_all_allows_admin(self, admin_client):
        """Test that /api/delete_all allows admin users."""
        response = await admin_client.post("/api/delete_all")
        # Should succeed or fail with a different error (not 401/403)
        assert response.status_code not in [401, 403]

    @pytest.mark.asyncio
    async def test_clear_allows_admin(self, admin_client):
        """Test that /api/clear allows admin users."""
        response = await admin_client.post("/api/clear")
        # Should succeed or fail with a different error (not 401/403)
        assert response.status_code not in [401, 403]

    @pytest.mark.asyncio
    async def test_compute_stats_allows_admin(self, admin_client):
        """Test that POST /api/stats allows admin users."""
        response = await admin_client.post("/api/stats")
        # Should succeed or fail with a different error (not 401/403)
        assert response.status_code not in [401, 403]

    @pytest.mark.asyncio
    async def test_index_db_allows_admin(self, admin_client):
        """Test that /api/index_db allows admin users."""
        response = await admin_client.post("/api/index_db")
        # Should succeed or fail with a different error (not 401/403)
        assert response.status_code not in [401, 403]


class TestPublicEndpointsRemainPublic:
    """Test that public endpoints remain accessible without authentication."""

    @pytest.mark.asyncio
    async def test_get_random_is_public(self, async_client):
        """Test that /api/get_random is still public."""
        response = await async_client.get("/api/get_random")
        # Should not return 401/403 (may return 404 if no data)
        assert response.status_code not in [401, 403]

    @pytest.mark.asyncio
    async def test_get_stats_is_public(self, async_client):
        """Test that GET /api/stats is still public."""
        response = await async_client.get("/api/stats")
        # Should not return 401/403
        assert response.status_code not in [401, 403]

    @pytest.mark.asyncio
    async def test_get_idioms_is_public(self, async_client):
        """Test that GET /api/idioms is still public."""
        response = await async_client.get("/api/idioms")
        # Should not return 401/403
        assert response.status_code not in [401, 403]

    @pytest.mark.asyncio
    async def test_get_quotes_is_public(self, async_client):
        """Test that GET /api/quotes is still public."""
        response = await async_client.get("/api/quotes")
        # Should not return 401/403
        assert response.status_code not in [401, 403]
