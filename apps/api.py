"""API configuration and routes."""

from django_matt import MattAPI

from apps.users.controllers import register_auth_routes

# Create the API instance
api = MattAPI(
    title="My API",
    version="1.0.0",
    description="A modern API built with django-matt",
)

# Register auth routes
register_auth_routes(api)


# Health check endpoint
@api.get("/health", tags=["Health"])
async def health_check(request) -> dict:
    """Health check endpoint."""
    return {"status": "healthy"}


# Example protected endpoint
@api.get("/protected", tags=["Example"])
async def protected_endpoint(request) -> dict:
    """Example protected endpoint - requires JWT auth."""
    from django_matt.auth import jwt_required

    @jwt_required
    async def handler(request):
        return {"message": f"Hello, {request.user.email}!"}

    return await handler(request)
