"""Invitation model for organization invitations."""

import uuid

from django.conf import settings
from django.db import models

from .membership_model import MembershipRole
from .organization_model import Organization


class InvitationStatus(models.TextChoices):
    """Invitation status."""

    PENDING = "pending", "Pending"
    ACCEPTED = "accepted", "Accepted"
    DECLINED = "declined", "Declined"
    EXPIRED = "expired", "Expired"


class Invitation(models.Model):
    """Invitation to join an organization."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(
        Organization, on_delete=models.CASCADE, related_name="invitations"
    )
    email = models.EmailField()
    role = models.CharField(
        max_length=20, choices=MembershipRole.choices, default=MembershipRole.MEMBER
    )
    status = models.CharField(
        max_length=20, choices=InvitationStatus.choices, default=InvitationStatus.PENDING
    )

    # Inviter
    invited_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="sent_invitations",
    )

    # Token for accepting invitation
    token = models.CharField(max_length=64, unique=True)

    # Expiration
    expires_at = models.DateTimeField()

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "invitations"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"Invitation for {self.email} to {self.organization.name}"
