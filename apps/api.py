"""API configuration and routes."""

from django_matt import MattAPI

from apps.users.controllers import register_auth_routes
from apps.organizations.controllers import register_org_routes

# Create the API instance
api = MattAPI(
    title="My B2B API",
    version="1.0.0",
    description="A B2B multi-tenant API built with django-matt",
)

# Register routes
register_auth_routes(api)
register_org_routes(api)


# Health check endpoint
@api.get("/health", tags=["Health"])
async def health_check(request) -> dict:
    """Health check endpoint."""
    return {"status": "healthy"}
