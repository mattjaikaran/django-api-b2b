"""API configuration and routes."""

from ninja import NinjaAPI

from apps.organizations.controllers import router as org_router
from apps.users.controllers import router as auth_router

# Create the API instance
api = NinjaAPI(
    title="My B2B API",
    version="1.0.0",
    description="A B2B multi-tenant API built with Django Ninja",
)

# Register routers
api.add_router("/auth", auth_router, tags=["Auth"])
api.add_router("/organizations", org_router, tags=["Organizations"])


# Health check endpoint
@api.get("/health", tags=["Health"])
def health_check(request) -> dict:
    """Health check endpoint."""
    return {"status": "healthy"}
