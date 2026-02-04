"""Tests for authentication endpoints."""

import json

import pytest
from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.mark.django_db
class TestAuthEndpoints:
    """Test authentication endpoints."""

    def test_register(self, api_client):
        """Test user registration."""
        response = api_client.post(
            "/api/auth/register",
            data=json.dumps(
                {
                    "email": "newuser@example.com",
                    "username": "newuser",
                    "password": "securepass123",
                    "first_name": "",
                    "last_name": "",
                }
            ),
            content_type="application/json",
        )
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "newuser@example.com"
        assert data["username"] == "newuser"

    def test_login(self, api_client, user):
        """Test user login."""
        response = api_client.post(
            "/api/auth/login",
            data=json.dumps(
                {
                    "email": "test@example.com",
                    "password": "testpass123",
                }
            ),
            content_type="application/json",
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data

    def test_login_invalid_credentials(self, api_client, user):
        """Test login with invalid credentials."""
        response = api_client.post(
            "/api/auth/login",
            data=json.dumps(
                {
                    "email": "test@example.com",
                    "password": "wrongpassword",
                }
            ),
            content_type="application/json",
        )
        assert response.status_code == 401

    def test_me_authenticated(self, authenticated_client, user):
        """Test getting current user when authenticated."""
        response = authenticated_client.get("/api/auth/me")
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == user.email

    def test_me_unauthenticated(self, api_client):
        """Test getting current user when not authenticated."""
        response = api_client.get("/api/auth/me")
        assert response.status_code == 401


@pytest.mark.django_db
class TestHealthEndpoint:
    """Test health check endpoint."""

    def test_health_check(self, api_client):
        """Test health check returns healthy status."""
        response = api_client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
