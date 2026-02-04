"""
CI test settings for myproject.

Uses PostgreSQL configured via environment variables for CI testing.
"""

from .settings import *  # noqa: F401, F403

# Disable DEBUG for tests
DEBUG = False

# Faster password hashing for tests
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
]
