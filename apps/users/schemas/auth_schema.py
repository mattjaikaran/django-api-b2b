"""Pydantic schemas for authentication endpoints."""

from pydantic import BaseModel, EmailStr


class LoginSchema(BaseModel):
    """Login request schema."""

    email: EmailStr
    password: str


class TokenSchema(BaseModel):
    """Token response schema."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshTokenSchema(BaseModel):
    """Refresh token request schema."""

    refresh_token: str
