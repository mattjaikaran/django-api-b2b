"""
Test settings for myproject.

Uses SQLite for fast local testing without requiring PostgreSQL.
"""

from .settings import *  # noqa: F401, F403

# Use SQLite for tests
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

# Faster password hashing for tests
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
]

# Disable DEBUG for tests
DEBUG = False

# Use a consistent secret key for tests
SECRET_KEY = "test-secret-key-not-for-production"
