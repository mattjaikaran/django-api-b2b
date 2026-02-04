"""Membership model for user-organization relationships."""

import uuid

from django.conf import settings
from django.db import models

from .organization_model import Organization
from .team_model import Team


class MembershipRole(models.TextChoices):
    """Membership roles."""

    OWNER = "owner", "Owner"
    ADMIN = "admin", "Admin"
    MEMBER = "member", "Member"
    VIEWER = "viewer", "Viewer"


class Membership(models.Model):
    """User membership in an organization."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="memberships"
    )
    organization = models.ForeignKey(
        Organization, on_delete=models.CASCADE, related_name="memberships"
    )
    role = models.CharField(
        max_length=20, choices=MembershipRole.choices, default=MembershipRole.MEMBER
    )

    # Team assignments (optional)
    teams = models.ManyToManyField(Team, blank=True, related_name="members")

    # Status
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "memberships"
        unique_together = ["user", "organization"]
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.user.email} @ {self.organization.name} ({self.role})"

    @property
    def is_owner(self) -> bool:
        return self.role == MembershipRole.OWNER

    @property
    def is_admin(self) -> bool:
        return self.role in [MembershipRole.OWNER, MembershipRole.ADMIN]
