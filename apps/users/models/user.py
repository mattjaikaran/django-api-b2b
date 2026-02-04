"""Custom user model."""

from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """Custom user model with email as the primary identifier."""

    email = models.EmailField(unique=True)

    # Optional: Add additional fields
    avatar_url = models.URLField(blank=True, null=True)
    bio = models.TextField(blank=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

    class Meta:
        db_table = "users"
        verbose_name = "user"
        verbose_name_plural = "users"

    def __str__(self) -> str:
        return self.email
