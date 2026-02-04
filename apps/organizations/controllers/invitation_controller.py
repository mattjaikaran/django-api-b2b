"""Invitation API controllers."""

import secrets
from datetime import timedelta
from uuid import UUID

from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone
from ninja import Router
from ninja.errors import HttpError
from ninja_jwt.authentication import JWTAuth

from ..models import Invitation, InvitationStatus, Membership
from ..schemas import InvitationCreateSchema, InvitationSchema, MembershipSchema
from .utils import get_membership_or_404, require_admin

User = get_user_model()
router = Router()


@router.get("/{org_id}/invitations", response=list[InvitationSchema], auth=JWTAuth())
def list_invitations(request, org_id: UUID) -> list[InvitationSchema]:
    """List pending invitations (admin only)."""
    membership = get_membership_or_404(request.auth, org_id)
    require_admin(membership)

    invitations = Invitation.objects.filter(
        organization_id=org_id, status=InvitationStatus.PENDING
    ).select_related("organization", "invited_by")

    result = []
    for inv in invitations:
        result.append(
            InvitationSchema(
                id=inv.id,
                organization_id=inv.organization_id,
                organization_name=inv.organization.name,
                email=inv.email,
                role=inv.role,
                status=inv.status,
                invited_by_email=inv.invited_by.email if inv.invited_by else None,
                expires_at=inv.expires_at,
                created_at=inv.created_at,
            )
        )
    return result


@router.post("/{org_id}/invitations", response=InvitationSchema, auth=JWTAuth())
def create_invitation(request, org_id: UUID, data: InvitationCreateSchema) -> InvitationSchema:
    """Invite a user to organization (admin only)."""
    membership = get_membership_or_404(request.auth, org_id)
    require_admin(membership)

    # Check if user already a member
    if User.objects.filter(email=data.email, memberships__organization_id=org_id).exists():
        raise HttpError(400, "User is already a member")

    # Check for existing pending invitation
    if Invitation.objects.filter(
        email=data.email, organization_id=org_id, status=InvitationStatus.PENDING
    ).exists():
        raise HttpError(400, "Invitation already pending for this email")

    invitation = Invitation.objects.create(
        organization_id=org_id,
        email=data.email,
        role=data.role,
        invited_by=request.auth,
        token=secrets.token_urlsafe(32),
        expires_at=timezone.now() + timedelta(days=7),
    )

    # TODO: Send invitation email

    return InvitationSchema(
        id=invitation.id,
        organization_id=invitation.organization_id,
        organization_name=membership.organization.name,
        email=invitation.email,
        role=invitation.role,
        status=invitation.status,
        invited_by_email=request.auth.email,
        expires_at=invitation.expires_at,
        created_at=invitation.created_at,
    )


@router.post("/invitations/{token}/accept", response=MembershipSchema, auth=JWTAuth())
def accept_invitation(request, token: str) -> MembershipSchema:
    """Accept an invitation."""
    try:
        invitation = Invitation.objects.select_related("organization").get(
            token=token, status=InvitationStatus.PENDING
        )
    except Invitation.DoesNotExist:
        raise HttpError(404, "Invalid or expired invitation")

    if invitation.expires_at < timezone.now():
        invitation.status = InvitationStatus.EXPIRED
        invitation.save()
        raise HttpError(400, "Invitation has expired")

    if invitation.email != request.auth.email:
        raise HttpError(403, "Invitation is for a different email")

    with transaction.atomic():
        # Create membership
        membership = Membership.objects.create(
            user=request.auth,
            organization=invitation.organization,
            role=invitation.role,
        )

        # Mark invitation as accepted
        invitation.status = InvitationStatus.ACCEPTED
        invitation.save()

    return MembershipSchema(
        id=membership.id,
        user_id=membership.user_id,
        user_email=request.auth.email,
        organization_id=membership.organization_id,
        organization_name=invitation.organization.name,
        role=membership.role,
        is_active=membership.is_active,
        created_at=membership.created_at,
    )


@router.delete("/{org_id}/invitations/{invitation_id}", auth=JWTAuth())
def cancel_invitation(request, org_id: UUID, invitation_id: UUID) -> dict:
    """Cancel an invitation (admin only)."""
    membership = get_membership_or_404(request.auth, org_id)
    require_admin(membership)

    try:
        invitation = Invitation.objects.get(
            id=invitation_id, organization_id=org_id, status=InvitationStatus.PENDING
        )
    except Invitation.DoesNotExist:
        raise HttpError(404, "Invitation not found")

    invitation.delete()
    return {"message": "Invitation cancelled"}
