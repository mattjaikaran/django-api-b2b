"""User API controllers."""

from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import check_password, make_password
from ninja import Router
from ninja.errors import HttpError
from ninja_jwt.authentication import JWTAuth
from ninja_jwt.tokens import RefreshToken

from .schemas import (
    ChangePasswordSchema,
    LoginSchema,
    RefreshTokenSchema,
    TokenSchema,
    UserCreateSchema,
    UserSchema,
    UserUpdateSchema,
)

User = get_user_model()
router = Router()


@router.post("/register", response=UserSchema)
def register(request, data: UserCreateSchema) -> UserSchema:
    """Register a new user."""
    # Check if email exists
    if User.objects.filter(email=data.email).exists():
        raise HttpError(400, "Email already registered")

    # Check if username exists
    if User.objects.filter(username=data.username).exists():
        raise HttpError(400, "Username already taken")

    # Create user
    user = User.objects.create(
        email=data.email,
        username=data.username,
        password=make_password(data.password),
        first_name=data.first_name,
        last_name=data.last_name,
    )

    return UserSchema.model_validate(user)


@router.post("/login", response=TokenSchema)
def login(request, data: LoginSchema) -> TokenSchema:
    """Login and get tokens."""
    try:
        user = User.objects.get(email=data.email)
    except User.DoesNotExist:
        raise HttpError(401, "Invalid credentials")

    if not check_password(data.password, user.password):
        raise HttpError(401, "Invalid credentials")

    if not user.is_active:
        raise HttpError(401, "Account is disabled")

    refresh = RefreshToken.for_user(user)
    return TokenSchema(
        access_token=str(refresh.access_token),
        refresh_token=str(refresh),
        token_type="bearer",
    )


@router.post("/refresh", response=TokenSchema)
def refresh(request, data: RefreshTokenSchema) -> TokenSchema:
    """Refresh access token."""
    try:
        refresh = RefreshToken(data.refresh_token)
        return TokenSchema(
            access_token=str(refresh.access_token),
            refresh_token=str(refresh),
            token_type="bearer",
        )
    except Exception as e:
        raise HttpError(401, str(e))


@router.get("/me", response=UserSchema, auth=JWTAuth())
def me(request) -> UserSchema:
    """Get current user profile."""
    return UserSchema.model_validate(request.auth)


@router.patch("/me", response=UserSchema, auth=JWTAuth())
def update_me(request, data: UserUpdateSchema) -> UserSchema:
    """Update current user profile."""
    user = request.auth
    update_data = data.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(user, field, value)

    user.save()
    return UserSchema.model_validate(user)


@router.post("/change-password", auth=JWTAuth())
def change_password(request, data: ChangePasswordSchema) -> dict:
    """Change password."""
    user = request.auth

    if not check_password(data.current_password, user.password):
        raise HttpError(400, "Current password is incorrect")

    user.password = make_password(data.new_password)
    user.save()

    return {"message": "Password changed successfully"}
