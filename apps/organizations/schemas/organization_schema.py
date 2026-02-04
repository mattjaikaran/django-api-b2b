"""Pydantic schemas for organization endpoints."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class OrganizationSchema(BaseModel):
    """Organization response schema."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    slug: str
    logo_url: str | None = None
    website: str | None = None
    plan: str
    created_at: datetime


class OrganizationCreateSchema(BaseModel):
    """Create organization schema."""

    name: str = Field(..., min_length=1, max_length=255)
    slug: str = Field(..., min_length=1, max_length=255, pattern=r"^[a-z0-9-]+$")
    logo_url: str | None = None
    website: str | None = None


class OrganizationUpdateSchema(BaseModel):
    """Update organization schema."""

    name: str | None = None
    logo_url: str | None = None
    website: str | None = None


class OrganizationWithRoleSchema(BaseModel):
    """Organization with user's role."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    slug: str
    logo_url: str | None = None
    plan: str
    role: str  # User's role in this org
    is_active: bool
