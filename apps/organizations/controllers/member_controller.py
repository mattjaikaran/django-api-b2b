"""Member API controllers."""

from uuid import UUID

from ninja import Router
from ninja.errors import HttpError
from ninja_jwt.authentication import JWTAuth

from ..models import Membership, MembershipRole
from ..schemas import MembershipSchema, MembershipUpdateSchema
from .utils import get_membership_or_404, require_admin

router = Router()


@router.get("/{org_id}/members", response=list[MembershipSchema], auth=JWTAuth())
def list_members(request, org_id: UUID) -> list[MembershipSchema]:
    """List members of an organization."""
    get_membership_or_404(request.auth, org_id)

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
    admin_membership = get_membership_or_404(request.auth, org_id)
    require_admin(admin_membership)

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
    admin_membership = get_membership_or_404(request.auth, org_id)
    require_admin(admin_membership)

    try:
        membership = Membership.objects.get(id=member_id, organization_id=org_id)
    except Membership.DoesNotExist:
        raise HttpError(404, "Member not found")

    # Can't remove owner
    if membership.is_owner:
        raise HttpError(400, "Cannot remove organization owner")

    membership.delete()
    return {"message": "Member removed"}
