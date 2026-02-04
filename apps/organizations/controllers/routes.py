"""Organization routes configuration."""

from ninja import Router

from .invitation_controller import router as invitation_router
from .member_controller import router as member_router
from .organization_controller import router as org_router
from .team_controller import router as team_router

# Main router that combines all organization-related routes
router = Router()

# Include all sub-routers
# Note: Each controller has its own router, they are combined here
# The main API will register this combined router under /organizations

__all__ = [
    "router",
    "org_router",
    "team_router",
    "member_router",
    "invitation_router",
]
