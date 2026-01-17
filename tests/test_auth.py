"""Tests for authentication endpoints."""

import pytest
from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.mark.django_db
class TestAuthEndpoints:
    """Test authentication endpoints."""

    async def test_register(self, api_client):
        """Test user registration."""
        response = await api_client.post(
            "/api/auth/register",
            data={
                "email": "newuser@example.com",
                "username": "newuser",
                "password": "securepass123",
            },
            content_type="application/json",
        )
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "newuser@example.com"
        assert data["username"] == "newuser"

    async def test_login(self, api_client, user):
        """Test user login."""
        response = await api_client.post(
            "/api/auth/login",
            data={
                "email": "test@example.com",
                "password": "testpass123",
            },
            content_type="application/json",
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data

    async def test_login_invalid_credentials(self, api_client, user):
        """Test login with invalid credentials."""
        response = await api_client.post(
            "/api/auth/login",
            data={
                "email": "test@example.com",
                "password": "wrongpassword",
            },
            content_type="application/json",
        )
        assert response.status_code == 401

    async def test_me_authenticated(self, authenticated_client, user):
        """Test getting current user when authenticated."""
        response = await authenticated_client.get("/api/auth/me")
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == user.email

    async def test_me_unauthenticated(self, api_client):
        """Test getting current user when not authenticated."""
        response = await api_client.get("/api/auth/me")
        assert response.status_code == 401
