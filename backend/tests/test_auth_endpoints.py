"""Tests for Authentication API endpoints."""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
class TestAuthEndpoints:
    """Test authentication API endpoints."""

    async def test_signup_success(self, async_client: AsyncClient):
        """Test successful user registration."""
        response = await async_client.post(
            "/auth/signup",
            json={
                "username": "newuser",
                "email": "newuser@example.com",
                "password": "securepassword123"
            }
        )

        assert response.status_code == 201
        data = response.json()

        assert "token" in data
        assert data["token"] is not None
        assert "user" in data
        assert data["user"]["username"] == "newuser"
        assert data["user"]["email"] == "newuser@example.com"
        assert data["user"]["energy"] == 10
        assert data["user"]["level"] == 1
        assert data["user"]["xp"] == 0

    async def test_signup_duplicate_email(self, async_client: AsyncClient):
        """Test signup with duplicate email fails."""
        # First signup
        await async_client.post(
            "/auth/signup",
            json={
                "username": "user1",
                "email": "duplicate@example.com",
                "password": "password123"
            }
        )

        # Try to signup with same email
        response = await async_client.post(
            "/auth/signup",
            json={
                "username": "user2",
                "email": "duplicate@example.com",
                "password": "password456"
            }
        )

        assert response.status_code == 409
        assert "email" in response.json()["detail"].lower()

    async def test_signup_duplicate_username(self, async_client: AsyncClient):
        """Test signup with duplicate username fails."""
        # First signup
        await async_client.post(
            "/auth/signup",
            json={
                "username": "sameuser",
                "email": "email1@example.com",
                "password": "password123"
            }
        )

        # Try to signup with same username
        response = await async_client.post(
            "/auth/signup",
            json={
                "username": "sameuser",
                "email": "email2@example.com",
                "password": "password456"
            }
        )

        assert response.status_code == 409
        assert "username" in response.json()["detail"].lower()

    async def test_login_success_with_email(self, async_client: AsyncClient):
        """Test successful login with email."""
        # First signup
        await async_client.post(
            "/auth/signup",
            json={
                "username": "loginuser",
                "email": "login@example.com",
                "password": "mypassword123"
            }
        )

        # Login with email
        response = await async_client.post(
            "/auth/login",
            json={
                "login": "login@example.com",
                "password": "mypassword123"
            }
        )

        assert response.status_code == 200
        data = response.json()

        assert "token" in data
        assert data["token"] is not None
        assert "user" in data
        assert data["user"]["email"] == "login@example.com"

    async def test_login_success_with_username(self, async_client: AsyncClient):
        """Test successful login with username."""
        # First signup
        await async_client.post(
            "/auth/signup",
            json={
                "username": "loginuser2",
                "email": "login2@example.com",
                "password": "mypassword456"
            }
        )

        # Login with username
        response = await async_client.post(
            "/auth/login",
            json={
                "login": "loginuser2",
                "password": "mypassword456"
            }
        )

        assert response.status_code == 200
        data = response.json()

        assert "token" in data
        assert data["user"]["username"] == "loginuser2"

    async def test_login_wrong_password(self, async_client: AsyncClient):
        """Test login with wrong password fails."""
        # First signup
        await async_client.post(
            "/auth/signup",
            json={
                "username": "secureuser",
                "email": "secure@example.com",
                "password": "correctpassword"
            }
        )

        # Try login with wrong password
        response = await async_client.post(
            "/auth/login",
            json={
                "login": "secure@example.com",
                "password": "wrongpassword"
            }
        )

        assert response.status_code == 401
        assert "credentials" in response.json()["detail"].lower()

    async def test_login_nonexistent_user(self, async_client: AsyncClient):
        """Test login with non-existent user fails."""
        response = await async_client.post(
            "/auth/login",
            json={
                "login": "ghost@example.com",
                "password": "anypassword"
            }
        )

        assert response.status_code == 401
        assert "credentials" in response.json()["detail"].lower()

    async def test_get_me_authenticated(self, authenticated_client: AsyncClient):
        """Test /auth/me endpoint with valid token."""
        response = await authenticated_client.get("/auth/me")

        assert response.status_code == 200
        data = response.json()

        assert "id" in data
        assert "username" in data
        assert "email" in data
        assert "energy" in data
        assert "level" in data
        assert "xp" in data

    async def test_get_me_unauthenticated(self, async_client: AsyncClient):
        """Test /auth/me endpoint without token fails."""
        response = await async_client.get("/auth/me")

        # Should fail without authentication
        assert response.status_code in [401, 403]

    async def test_get_me_invalid_token(self, async_client: AsyncClient):
        """Test /auth/me endpoint with invalid token fails."""
        async_client.headers.update({"Authorization": "Bearer invalid_token_xyz"})

        response = await async_client.get("/auth/me")

        assert response.status_code in [401, 403]

    async def test_get_self_authenticated(self, authenticated_client: AsyncClient):
        """Test /self endpoint with valid token."""
        response = await authenticated_client.get("/self")

        assert response.status_code == 200
        data = response.json()

        assert "id" in data
        assert "username" in data
        assert "email" in data
        assert "energy" in data
        assert "max_energy" in data
        assert "level" in data
        assert "xp" in data
        assert "max_xp" in data
        assert data["max_xp"] == data["level"] * 10  # max_xp formula

    async def test_get_self_unauthenticated(self, async_client: AsyncClient):
        """Test /self endpoint without token fails."""
        response = await async_client.get("/self")

        assert response.status_code in [401, 403]

    async def test_token_contains_user_info(self, async_client: AsyncClient):
        """Test that JWT token can be decoded and contains user info."""
        # Signup and get token
        response = await async_client.post(
            "/auth/signup",
            json={
                "username": "tokentest",
                "email": "token@example.com",
                "password": "tokenpass123"
            }
        )

        assert response.status_code == 201
        token = response.json()["token"]

        # Use token to access protected endpoint
        async_client.headers.update({"Authorization": f"Bearer {token}"})
        response = await async_client.get("/auth/me")

        assert response.status_code == 200
        user_data = response.json()
        assert user_data["username"] == "tokentest"
        assert user_data["email"] == "token@example.com"

    async def test_signup_email_case_insensitive(self, async_client: AsyncClient):
        """Test that email is stored in lowercase."""
        response = await async_client.post(
            "/auth/signup",
            json={
                "username": "casetest",
                "email": "CaseSensitive@Example.COM",
                "password": "password123"
            }
        )

        assert response.status_code == 201
        data = response.json()

        # Email should be lowercased
        assert data["user"]["email"] == "casesensitive@example.com"

    async def test_login_email_case_insensitive(self, async_client: AsyncClient):
        """Test that login with different case email works."""
        # Signup with lowercase
        await async_client.post(
            "/auth/signup",
            json={
                "username": "caseuser",
                "email": "caseuser@example.com",
                "password": "password123"
            }
        )

        # Login with uppercase email
        response = await async_client.post(
            "/auth/login",
            json={
                "login": "CASEUSER@EXAMPLE.COM",
                "password": "password123"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["user"]["email"] == "caseuser@example.com"
