"""Organization API controllers."""

from uuid import UUID

from django.db import transaction
from ninja import Router
from ninja.errors import HttpError
from ninja_jwt.authentication import JWTAuth

from ..models import Membership, MembershipRole, Organization
from ..schemas import (
    OrganizationCreateSchema,
    OrganizationSchema,
    OrganizationUpdateSchema,
    OrganizationWithRoleSchema,
)
from .utils import get_membership_or_404, require_admin, require_owner

router = Router()


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
    membership = get_membership_or_404(request.auth, org_id)
    return OrganizationSchema.model_validate(membership.organization)


@router.patch("/{org_id}", response=OrganizationSchema, auth=JWTAuth())
def update_organization(
    request, org_id: UUID, data: OrganizationUpdateSchema
) -> OrganizationSchema:
    """Update organization (admin only)."""
    membership = get_membership_or_404(request.auth, org_id)
    require_admin(membership)

    org = membership.organization
    update_data = data.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(org, field, value)

    org.save()
    return OrganizationSchema.model_validate(org)


@router.delete("/{org_id}", auth=JWTAuth())
def delete_organization(request, org_id: UUID) -> dict:
    """Delete organization (owner only)."""
    membership = get_membership_or_404(request.auth, org_id)
    require_owner(membership)

    membership.organization.delete()
    return {"message": "Organization deleted"}
