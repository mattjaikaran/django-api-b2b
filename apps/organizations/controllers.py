"""Organization API controllers."""

import secrets
from datetime import timedelta
from uuid import UUID

from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone
from django.utils.text import slugify

from django_matt import MattAPI
from django_matt.auth import jwt_required
from django_matt.core import APIController
from django_matt.core.errors import APIError, NotFoundAPIError, ValidationAPIError

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


class OrganizationController(APIController):
    """Organization management controller."""

    tags = ["Organizations"]

    @staticmethod
    @jwt_required
    async def list_organizations(request) -> list[OrganizationWithRoleSchema]:
        """List organizations the current user belongs to."""
        memberships = Membership.objects.filter(
            user=request.user, is_active=True
        ).select_related("organization")

        result = []
        async for membership in memberships:
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

    @staticmethod
    @jwt_required
    async def create_organization(request, data: OrganizationCreateSchema) -> OrganizationSchema:
        """Create a new organization."""
        # Check if slug is taken
        if await Organization.objects.filter(slug=data.slug).aexists():
            raise ValidationAPIError("Organization slug already taken")

        async with transaction.atomic():
            # Create organization
            org = await Organization.objects.acreate(
                name=data.name,
                slug=data.slug,
                logo_url=data.logo_url,
                website=data.website,
            )

            # Add creator as owner
            await Membership.objects.acreate(
                user=request.user,
                organization=org,
                role=MembershipRole.OWNER,
            )

        return OrganizationSchema.model_validate(org)

    @staticmethod
    @jwt_required
    async def get_organization(request, org_id: UUID) -> OrganizationSchema:
        """Get organization details."""
        try:
            membership = await Membership.objects.select_related("organization").aget(
                user=request.user, organization_id=org_id, is_active=True
            )
        except Membership.DoesNotExist:
            raise NotFoundAPIError("Organization not found")

        return OrganizationSchema.model_validate(membership.organization)

    @staticmethod
    @jwt_required
    async def update_organization(
        request, org_id: UUID, data: OrganizationUpdateSchema
    ) -> OrganizationSchema:
        """Update organization (admin only)."""
        try:
            membership = await Membership.objects.select_related("organization").aget(
                user=request.user, organization_id=org_id, is_active=True
            )
        except Membership.DoesNotExist:
            raise NotFoundAPIError("Organization not found")

        if not membership.is_admin:
            raise APIError(status_code=403, message="Admin access required")

        org = membership.organization
        update_data = data.model_dump(exclude_unset=True)

        for field, value in update_data.items():
            setattr(org, field, value)

        await org.asave()
        return OrganizationSchema.model_validate(org)

    @staticmethod
    @jwt_required
    async def delete_organization(request, org_id: UUID) -> dict:
        """Delete organization (owner only)."""
        try:
            membership = await Membership.objects.select_related("organization").aget(
                user=request.user, organization_id=org_id, is_active=True
            )
        except Membership.DoesNotExist:
            raise NotFoundAPIError("Organization not found")

        if not membership.is_owner:
            raise APIError(status_code=403, message="Owner access required")

        await membership.organization.adelete()
        return {"message": "Organization deleted"}


class TeamController(APIController):
    """Team management controller."""

    tags = ["Teams"]

    @staticmethod
    @jwt_required
    async def list_teams(request, org_id: UUID) -> list[TeamSchema]:
        """List teams in an organization."""
        try:
            await Membership.objects.aget(
                user=request.user, organization_id=org_id, is_active=True
            )
        except Membership.DoesNotExist:
            raise NotFoundAPIError("Organization not found")

        teams = Team.objects.filter(organization_id=org_id)
        return [TeamSchema.model_validate(team) async for team in teams]

    @staticmethod
    @jwt_required
    async def create_team(request, org_id: UUID, data: TeamCreateSchema) -> TeamSchema:
        """Create a new team (admin only)."""
        try:
            membership = await Membership.objects.aget(
                user=request.user, organization_id=org_id, is_active=True
            )
        except Membership.DoesNotExist:
            raise NotFoundAPIError("Organization not found")

        if not membership.is_admin:
            raise APIError(status_code=403, message="Admin access required")

        # Check if slug is taken in this org
        if await Team.objects.filter(organization_id=org_id, slug=data.slug).aexists():
            raise ValidationAPIError("Team slug already taken in this organization")

        team = await Team.objects.acreate(
            organization_id=org_id,
            name=data.name,
            slug=data.slug,
            description=data.description,
        )

        return TeamSchema.model_validate(team)

    @staticmethod
    @jwt_required
    async def update_team(
        request, org_id: UUID, team_id: UUID, data: TeamUpdateSchema
    ) -> TeamSchema:
        """Update a team (admin only)."""
        try:
            membership = await Membership.objects.aget(
                user=request.user, organization_id=org_id, is_active=True
            )
        except Membership.DoesNotExist:
            raise NotFoundAPIError("Organization not found")

        if not membership.is_admin:
            raise APIError(status_code=403, message="Admin access required")

        try:
            team = await Team.objects.aget(id=team_id, organization_id=org_id)
        except Team.DoesNotExist:
            raise NotFoundAPIError("Team not found")

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(team, field, value)

        await team.asave()
        return TeamSchema.model_validate(team)

    @staticmethod
    @jwt_required
    async def delete_team(request, org_id: UUID, team_id: UUID) -> dict:
        """Delete a team (admin only)."""
        try:
            membership = await Membership.objects.aget(
                user=request.user, organization_id=org_id, is_active=True
            )
        except Membership.DoesNotExist:
            raise NotFoundAPIError("Organization not found")

        if not membership.is_admin:
            raise APIError(status_code=403, message="Admin access required")

        try:
            team = await Team.objects.aget(id=team_id, organization_id=org_id)
        except Team.DoesNotExist:
            raise NotFoundAPIError("Team not found")

        await team.adelete()
        return {"message": "Team deleted"}


class MemberController(APIController):
    """Member management controller."""

    tags = ["Members"]

    @staticmethod
    @jwt_required
    async def list_members(request, org_id: UUID) -> list[MembershipSchema]:
        """List members of an organization."""
        try:
            await Membership.objects.aget(
                user=request.user, organization_id=org_id, is_active=True
            )
        except Membership.DoesNotExist:
            raise NotFoundAPIError("Organization not found")

        memberships = Membership.objects.filter(organization_id=org_id).select_related(
            "user", "organization"
        )

        result = []
        async for m in memberships:
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

    @staticmethod
    @jwt_required
    async def update_member(
        request, org_id: UUID, member_id: UUID, data: MembershipUpdateSchema
    ) -> MembershipSchema:
        """Update a member's role (admin only)."""
        try:
            admin_membership = await Membership.objects.aget(
                user=request.user, organization_id=org_id, is_active=True
            )
        except Membership.DoesNotExist:
            raise NotFoundAPIError("Organization not found")

        if not admin_membership.is_admin:
            raise APIError(status_code=403, message="Admin access required")

        try:
            membership = await Membership.objects.select_related("user", "organization").aget(
                id=member_id, organization_id=org_id
            )
        except Membership.DoesNotExist:
            raise NotFoundAPIError("Member not found")

        # Can't change owner's role
        if membership.is_owner and data.role and data.role != MembershipRole.OWNER:
            raise ValidationAPIError("Cannot change owner's role")

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(membership, field, value)

        await membership.asave()

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

    @staticmethod
    @jwt_required
    async def remove_member(request, org_id: UUID, member_id: UUID) -> dict:
        """Remove a member from organization (admin only)."""
        try:
            admin_membership = await Membership.objects.aget(
                user=request.user, organization_id=org_id, is_active=True
            )
        except Membership.DoesNotExist:
            raise NotFoundAPIError("Organization not found")

        if not admin_membership.is_admin:
            raise APIError(status_code=403, message="Admin access required")

        try:
            membership = await Membership.objects.aget(id=member_id, organization_id=org_id)
        except Membership.DoesNotExist:
            raise NotFoundAPIError("Member not found")

        # Can't remove owner
        if membership.is_owner:
            raise ValidationAPIError("Cannot remove organization owner")

        await membership.adelete()
        return {"message": "Member removed"}


class InvitationController(APIController):
    """Invitation management controller."""

    tags = ["Invitations"]

    @staticmethod
    @jwt_required
    async def list_invitations(request, org_id: UUID) -> list[InvitationSchema]:
        """List pending invitations (admin only)."""
        try:
            membership = await Membership.objects.aget(
                user=request.user, organization_id=org_id, is_active=True
            )
        except Membership.DoesNotExist:
            raise NotFoundAPIError("Organization not found")

        if not membership.is_admin:
            raise APIError(status_code=403, message="Admin access required")

        invitations = Invitation.objects.filter(
            organization_id=org_id, status=InvitationStatus.PENDING
        ).select_related("organization", "invited_by")

        result = []
        async for inv in invitations:
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

    @staticmethod
    @jwt_required
    async def create_invitation(
        request, org_id: UUID, data: InvitationCreateSchema
    ) -> InvitationSchema:
        """Invite a user to organization (admin only)."""
        try:
            membership = await Membership.objects.select_related("organization").aget(
                user=request.user, organization_id=org_id, is_active=True
            )
        except Membership.DoesNotExist:
            raise NotFoundAPIError("Organization not found")

        if not membership.is_admin:
            raise APIError(status_code=403, message="Admin access required")

        # Check if user already a member
        if await User.objects.filter(
            email=data.email, memberships__organization_id=org_id
        ).aexists():
            raise ValidationAPIError("User is already a member")

        # Check for existing pending invitation
        if await Invitation.objects.filter(
            email=data.email, organization_id=org_id, status=InvitationStatus.PENDING
        ).aexists():
            raise ValidationAPIError("Invitation already pending for this email")

        invitation = await Invitation.objects.acreate(
            organization_id=org_id,
            email=data.email,
            role=data.role,
            invited_by=request.user,
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
            invited_by_email=request.user.email,
            expires_at=invitation.expires_at,
            created_at=invitation.created_at,
        )

    @staticmethod
    @jwt_required
    async def accept_invitation(request, token: str) -> MembershipSchema:
        """Accept an invitation."""
        try:
            invitation = await Invitation.objects.select_related("organization").aget(
                token=token, status=InvitationStatus.PENDING
            )
        except Invitation.DoesNotExist:
            raise NotFoundAPIError("Invalid or expired invitation")

        if invitation.expires_at < timezone.now():
            invitation.status = InvitationStatus.EXPIRED
            await invitation.asave()
            raise APIError(status_code=400, message="Invitation has expired")

        if invitation.email != request.user.email:
            raise APIError(status_code=403, message="Invitation is for a different email")

        async with transaction.atomic():
            # Create membership
            membership = await Membership.objects.acreate(
                user=request.user,
                organization=invitation.organization,
                role=invitation.role,
            )

            # Mark invitation as accepted
            invitation.status = InvitationStatus.ACCEPTED
            await invitation.asave()

        return MembershipSchema(
            id=membership.id,
            user_id=membership.user_id,
            user_email=request.user.email,
            organization_id=membership.organization_id,
            organization_name=invitation.organization.name,
            role=membership.role,
            is_active=membership.is_active,
            created_at=membership.created_at,
        )

    @staticmethod
    @jwt_required
    async def cancel_invitation(request, org_id: UUID, invitation_id: UUID) -> dict:
        """Cancel an invitation (admin only)."""
        try:
            membership = await Membership.objects.aget(
                user=request.user, organization_id=org_id, is_active=True
            )
        except Membership.DoesNotExist:
            raise NotFoundAPIError("Organization not found")

        if not membership.is_admin:
            raise APIError(status_code=403, message="Admin access required")

        try:
            invitation = await Invitation.objects.aget(
                id=invitation_id, organization_id=org_id, status=InvitationStatus.PENDING
            )
        except Invitation.DoesNotExist:
            raise NotFoundAPIError("Invitation not found")

        await invitation.adelete()
        return {"message": "Invitation cancelled"}


def register_org_routes(api: MattAPI) -> None:
    """Register organization routes on the API."""
    # Organizations
    api.get("/organizations", response=list[OrganizationWithRoleSchema])(
        OrganizationController.list_organizations
    )
    api.post("/organizations", response=OrganizationSchema)(
        OrganizationController.create_organization
    )
    api.get("/organizations/{org_id}", response=OrganizationSchema)(
        OrganizationController.get_organization
    )
    api.patch("/organizations/{org_id}", response=OrganizationSchema)(
        OrganizationController.update_organization
    )
    api.delete("/organizations/{org_id}")(OrganizationController.delete_organization)

    # Teams
    api.get("/organizations/{org_id}/teams", response=list[TeamSchema])(
        TeamController.list_teams
    )
    api.post("/organizations/{org_id}/teams", response=TeamSchema)(
        TeamController.create_team
    )
    api.patch("/organizations/{org_id}/teams/{team_id}", response=TeamSchema)(
        TeamController.update_team
    )
    api.delete("/organizations/{org_id}/teams/{team_id}")(TeamController.delete_team)

    # Members
    api.get("/organizations/{org_id}/members", response=list[MembershipSchema])(
        MemberController.list_members
    )
    api.patch("/organizations/{org_id}/members/{member_id}", response=MembershipSchema)(
        MemberController.update_member
    )
    api.delete("/organizations/{org_id}/members/{member_id}")(MemberController.remove_member)

    # Invitations
    api.get("/organizations/{org_id}/invitations", response=list[InvitationSchema])(
        InvitationController.list_invitations
    )
    api.post("/organizations/{org_id}/invitations", response=InvitationSchema)(
        InvitationController.create_invitation
    )
    api.post("/invitations/{token}/accept", response=MembershipSchema)(
        InvitationController.accept_invitation
    )
    api.delete("/organizations/{org_id}/invitations/{invitation_id}")(
        InvitationController.cancel_invitation
    )
