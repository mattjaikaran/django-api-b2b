"""Team model within an organization."""

import uuid

from django.db import models

from .organization import Organization


class Team(models.Model):
    """Team within an organization."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name="teams")
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255)
    description = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "teams"
        unique_together = ["organization", "slug"]
        ordering = ["name"]

    def __str__(self) -> str:
        return f"{self.organization.name} / {self.name}"
