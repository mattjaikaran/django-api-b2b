"""Pydantic schemas for user endpoints."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserSchema(BaseModel):
    """User response schema."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    email: EmailStr
    username: str
    first_name: str = ""
    last_name: str = ""
    avatar_url: str | None = None
    bio: str = ""
    is_active: bool = True
    date_joined: datetime


class UserCreateSchema(BaseModel):
    """User registration schema."""

    email: EmailStr
    username: str = Field(..., min_length=3, max_length=150)
    password: str = Field(..., min_length=8)
    first_name: str = ""
    last_name: str = ""


class UserUpdateSchema(BaseModel):
    """User update schema."""

    first_name: str | None = None
    last_name: str | None = None
    avatar_url: str | None = None
    bio: str | None = None


class ChangePasswordSchema(BaseModel):
    """Change password schema."""

    current_password: str
    new_password: str = Field(..., min_length=8)
