"""Utility functions for organization controllers."""

from uuid import UUID

from ninja.errors import HttpError

from ..models import Membership


def get_membership_or_404(user, org_id: UUID) -> Membership:
    """Get membership or raise 404."""
    try:
        return Membership.objects.select_related("organization").get(
            user=user, organization_id=org_id, is_active=True
        )
    except Membership.DoesNotExist:
        raise HttpError(404, "Organization not found")


def require_admin(membership: Membership) -> None:
    """Require admin access or raise 403."""
    if not membership.is_admin:
        raise HttpError(403, "Admin access required")


def require_owner(membership: Membership) -> None:
    """Require owner access or raise 403."""
    if not membership.is_owner:
        raise HttpError(403, "Owner access required")
