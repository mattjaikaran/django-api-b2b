"""Organization model for multi-tenancy."""

import uuid

from django.db import models


class Organization(models.Model):
    """Organization model for multi-tenancy."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True)
    logo_url = models.URLField(blank=True, null=True)
    website = models.URLField(blank=True, null=True)

    # Billing
    stripe_customer_id = models.CharField(max_length=255, blank=True, null=True)
    plan = models.CharField(max_length=50, default="free")

    # Settings
    settings = models.JSONField(default=dict, blank=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "organizations"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return self.name
