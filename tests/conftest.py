"""Pytest configuration and fixtures."""

import pytest
from django.contrib.auth import get_user_model
from django.test import Client
from ninja_jwt.tokens import RefreshToken

User = get_user_model()


@pytest.fixture
def user(db):
    """Create a test user."""
    return User.objects.create_user(
        email="test@example.com",
        username="testuser",
        password="testpass123",
    )


@pytest.fixture
def admin_user(db):
    """Create an admin user."""
    return User.objects.create_superuser(
        email="admin@example.com",
        username="admin",
        password="adminpass123",
    )


@pytest.fixture
def api_client():
    """Create an API test client."""
    return Client()


@pytest.fixture
def authenticated_client(api_client, user):
    """Create an authenticated API client."""
    refresh = RefreshToken.for_user(user)
    api_client.defaults["HTTP_AUTHORIZATION"] = f"Bearer {refresh.access_token}"
    return api_client
