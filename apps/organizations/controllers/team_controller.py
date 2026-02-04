"""Team API controllers."""

from uuid import UUID

from ninja import Router
from ninja.errors import HttpError
from ninja_jwt.authentication import JWTAuth

from ..models import Team
from ..schemas import TeamCreateSchema, TeamSchema, TeamUpdateSchema
from .utils import get_membership_or_404, require_admin

router = Router()


@router.get("/{org_id}/teams", response=list[TeamSchema], auth=JWTAuth())
def list_teams(request, org_id: UUID) -> list[TeamSchema]:
    """List teams in an organization."""
    get_membership_or_404(request.auth, org_id)
    teams = Team.objects.filter(organization_id=org_id)
    return [TeamSchema.model_validate(team) for team in teams]


@router.post("/{org_id}/teams", response=TeamSchema, auth=JWTAuth())
def create_team(request, org_id: UUID, data: TeamCreateSchema) -> TeamSchema:
    """Create a new team (admin only)."""
    membership = get_membership_or_404(request.auth, org_id)
    require_admin(membership)

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
    membership = get_membership_or_404(request.auth, org_id)
    require_admin(membership)

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
    membership = get_membership_or_404(request.auth, org_id)
    require_admin(membership)

    try:
        team = Team.objects.get(id=team_id, organization_id=org_id)
    except Team.DoesNotExist:
        raise HttpError(404, "Team not found")

    team.delete()
    return {"message": "Team deleted"}
