"""Pytest configuration and fixtures."""

import pytest
from django.contrib.auth import get_user_model

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
    from django.test import AsyncClient

    return AsyncClient()


@pytest.fixture
def authenticated_client(api_client, user):
    """Create an authenticated API client."""
    from django_matt.auth import create_token_pair

    tokens = create_token_pair(user)
    api_client.defaults["HTTP_AUTHORIZATION"] = f"Bearer {tokens['access_token']}"
    return api_client
