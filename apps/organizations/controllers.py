"""Organization API controllers."""

import secrets
from datetime import timedelta
from uuid import UUID

from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone
from ninja import Router
from ninja.errors import HttpError
from ninja_jwt.authentication import JWTAuth

from .models import Invitation, InvitationStatus, Membership, MembershipRole, Organization, Team
from .schemas import (
    InvitationCreateSchema,
    InvitationSchema,
    MembershipSchema,
    MembershipUpdateSchema,
    OrganizationCreateSchema,
    OrganizationSchema,
    OrganizationUpdateSchema,
    OrganizationWithRoleSchema,
    TeamCreateSchema,
    TeamSchema,
    TeamUpdateSchema,
)

User = get_user_model()
router = Router()


# =============================================================================
# Organization endpoints
# =============================================================================


@router.get("/", response=list[OrganizationWithRoleSchema], auth=JWTAuth())
def list_organizations(request) -> list[OrganizationWithRoleSchema]:
    """List organizations the current user belongs to."""
    memberships = Membership.objects.filter(user=request.auth, is_active=True).select_related(
        "organization"
    )

    result = []
    for membership in memberships:
        org = membership.organization
        result.append(
            OrganizationWithRoleSchema(
                id=org.id,
                name=org.name,
                slug=org.slug,
                logo_url=org.logo_url,
                plan=org.plan,
                role=membership.role,
                is_active=membership.is_active,
            )
        )
    return result


@router.post("/", response=OrganizationSchema, auth=JWTAuth())
def create_organization(request, data: OrganizationCreateSchema) -> OrganizationSchema:
    """Create a new organization."""
    # Check if slug is taken
    if Organization.objects.filter(slug=data.slug).exists():
        raise HttpError(400, "Organization slug already taken")

    with transaction.atomic():
        # Create organization
        org = Organization.objects.create(
            name=data.name,
            slug=data.slug,
            logo_url=data.logo_url,
            website=data.website,
        )

        # Add creator as owner
        Membership.objects.create(
            user=request.auth,
            organization=org,
            role=MembershipRole.OWNER,
        )

    return OrganizationSchema.model_validate(org)


@router.get("/{org_id}", response=OrganizationSchema, auth=JWTAuth())
def get_organization(request, org_id: UUID) -> OrganizationSchema:
    """Get organization details."""
    try:
        membership = Membership.objects.select_related("organization").get(
            user=request.auth, organization_id=org_id, is_active=True
        )
    except Membership.DoesNotExist:
        raise HttpError(404, "Organization not found")

    return OrganizationSchema.model_validate(membership.organization)


@router.patch("/{org_id}", response=OrganizationSchema, auth=JWTAuth())
def update_organization(
    request, org_id: UUID, data: OrganizationUpdateSchema
) -> OrganizationSchema:
    """Update organization (admin only)."""
    try:
        membership = Membership.objects.select_related("organization").get(
            user=request.auth, organization_id=org_id, is_active=True
        )
    except Membership.DoesNotExist:
        raise HttpError(404, "Organization not found")

    if not membership.is_admin:
        raise HttpError(403, "Admin access required")

    org = membership.organization
    update_data = data.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(org, field, value)

    org.save()
    return OrganizationSchema.model_validate(org)


@router.delete("/{org_id}", auth=JWTAuth())
def delete_organization(request, org_id: UUID) -> dict:
    """Delete organization (owner only)."""
    try:
        membership = Membership.objects.select_related("organization").get(
            user=request.auth, organization_id=org_id, is_active=True
        )
    except Membership.DoesNotExist:
        raise HttpError(404, "Organization not found")

    if not membership.is_owner:
        raise HttpError(403, "Owner access required")

    membership.organization.delete()
    return {"message": "Organization deleted"}


# =============================================================================
# Team endpoints
# =============================================================================


@router.get("/{org_id}/teams", response=list[TeamSchema], auth=JWTAuth())
def list_teams(request, org_id: UUID) -> list[TeamSchema]:
    """List teams in an organization."""
    try:
        Membership.objects.get(user=request.auth, organization_id=org_id, is_active=True)
    except Membership.DoesNotExist:
        raise HttpError(404, "Organization not found")

    teams = Team.objects.filter(organization_id=org_id)
    return [TeamSchema.model_validate(team) for team in teams]


@router.post("/{org_id}/teams", response=TeamSchema, auth=JWTAuth())
def create_team(request, org_id: UUID, data: TeamCreateSchema) -> TeamSchema:
    """Create a new team (admin only)."""
    try:
        membership = Membership.objects.get(
            user=request.auth, organization_id=org_id, is_active=True
        )
    except Membership.DoesNotExist:
        raise HttpError(404, "Organization not found")

    if not membership.is_admin:
        raise HttpError(403, "Admin access required")

    # Check if slug is taken in this org
    if Team.objects.filter(organization_id=org_id, slug=data.slug).exists():
        raise HttpError(400, "Team slug already taken in this organization")

    team = Team.objects.create(
        organization_id=org_id,
        name=data.name,
        slug=data.slug,
        description=data.description,
    )

    return TeamSchema.model_validate(team)


@router.patch("/{org_id}/teams/{team_id}", response=TeamSchema, auth=JWTAuth())
def update_team(request, org_id: UUID, team_id: UUID, data: TeamUpdateSchema) -> TeamSchema:
    """Update a team (admin only)."""
    try:
        membership = Membership.objects.get(
            user=request.auth, organization_id=org_id, is_active=True
        )
    except Membership.DoesNotExist:
        raise HttpError(404, "Organization not found")

    if not membership.is_admin:
        raise HttpError(403, "Admin access required")

    try:
        team = Team.objects.get(id=team_id, organization_id=org_id)
    except Team.DoesNotExist:
        raise HttpError(404, "Team not found")

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(team, field, value)

    team.save()
    return TeamSchema.model_validate(team)


@router.delete("/{org_id}/teams/{team_id}", auth=JWTAuth())
def delete_team(request, org_id: UUID, team_id: UUID) -> dict:
    """Delete a team (admin only)."""
    try:
        membership = Membership.objects.get(
            user=request.auth, organization_id=org_id, is_active=True
        )
    except Membership.DoesNotExist:
        raise HttpError(404, "Organization not found")

    if not membership.is_admin:
        raise HttpError(403, "Admin access required")

    try:
        team = Team.objects.get(id=team_id, organization_id=org_id)
    except Team.DoesNotExist:
        raise HttpError(404, "Team not found")

    team.delete()
    return {"message": "Team deleted"}


# =============================================================================
# Member endpoints
# =============================================================================


@router.get("/{org_id}/members", response=list[MembershipSchema], auth=JWTAuth())
def list_members(request, org_id: UUID) -> list[MembershipSchema]:
    """List members of an organization."""
    try:
        Membership.objects.get(user=request.auth, organization_id=org_id, is_active=True)
    except Membership.DoesNotExist:
        raise HttpError(404, "Organization not found")

    memberships = Membership.objects.filter(organization_id=org_id).select_related(
        "user", "organization"
    )

    result = []
    for m in memberships:
        result.append(
            MembershipSchema(
                id=m.id,
                user_id=m.user_id,
                user_email=m.user.email,
                organization_id=m.organization_id,
                organization_name=m.organization.name,
                role=m.role,
                is_active=m.is_active,
                created_at=m.created_at,
            )
        )
    return result


@router.patch("/{org_id}/members/{member_id}", response=MembershipSchema, auth=JWTAuth())
def update_member(
    request, org_id: UUID, member_id: UUID, data: MembershipUpdateSchema
) -> MembershipSchema:
    """Update a member's role (admin only)."""
    try:
        admin_membership = Membership.objects.get(
            user=request.auth, organization_id=org_id, is_active=True
        )
    except Membership.DoesNotExist:
        raise HttpError(404, "Organization not found")

    if not admin_membership.is_admin:
        raise HttpError(403, "Admin access required")

    try:
        membership = Membership.objects.select_related("user", "organization").get(
            id=member_id, organization_id=org_id
        )
    except Membership.DoesNotExist:
        raise HttpError(404, "Member not found")

    # Can't change owner's role
    if membership.is_owner and data.role and data.role != MembershipRole.OWNER:
        raise HttpError(400, "Cannot change owner's role")

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(membership, field, value)

    membership.save()

    return MembershipSchema(
        id=membership.id,
        user_id=membership.user_id,
        user_email=membership.user.email,
        organization_id=membership.organization_id,
        organization_name=membership.organization.name,
        role=membership.role,
        is_active=membership.is_active,
        created_at=membership.created_at,
    )


@router.delete("/{org_id}/members/{member_id}", auth=JWTAuth())
def remove_member(request, org_id: UUID, member_id: UUID) -> dict:
    """Remove a member from organization (admin only)."""
    try:
        admin_membership = Membership.objects.get(
            user=request.auth, organization_id=org_id, is_active=True
        )
    except Membership.DoesNotExist:
        raise HttpError(404, "Organization not found")

    if not admin_membership.is_admin:
        raise HttpError(403, "Admin access required")

    try:
        membership = Membership.objects.get(id=member_id, organization_id=org_id)
    except Membership.DoesNotExist:
        raise HttpError(404, "Member not found")

    # Can't remove owner
    if membership.is_owner:
        raise HttpError(400, "Cannot remove organization owner")

    membership.delete()
    return {"message": "Member removed"}


# =============================================================================
# Invitation endpoints
# =============================================================================


@router.get("/{org_id}/invitations", response=list[InvitationSchema], auth=JWTAuth())
def list_invitations(request, org_id: UUID) -> list[InvitationSchema]:
    """List pending invitations (admin only)."""
    try:
        membership = Membership.objects.get(
            user=request.auth, organization_id=org_id, is_active=True
        )
    except Membership.DoesNotExist:
        raise HttpError(404, "Organization not found")

    if not membership.is_admin:
        raise HttpError(403, "Admin access required")

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
    try:
        membership = Membership.objects.select_related("organization").get(
            user=request.auth, organization_id=org_id, is_active=True
        )
    except Membership.DoesNotExist:
        raise HttpError(404, "Organization not found")

    if not membership.is_admin:
        raise HttpError(403, "Admin access required")

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
    try:
        membership = Membership.objects.get(
            user=request.auth, organization_id=org_id, is_active=True
        )
    except Membership.DoesNotExist:
        raise HttpError(404, "Organization not found")

    if not membership.is_admin:
        raise HttpError(403, "Admin access required")

    try:
        invitation = Invitation.objects.get(
            id=invitation_id, organization_id=org_id, status=InvitationStatus.PENDING
        )
    except Invitation.DoesNotExist:
        raise HttpError(404, "Invitation not found")

    invitation.delete()
    return {"message": "Invitation cancelled"}
