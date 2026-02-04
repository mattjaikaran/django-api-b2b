"""Pydantic schemas for team endpoints."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class TeamSchema(BaseModel):
    """Team response schema."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    organization_id: UUID
    name: str
    slug: str
    description: str
    created_at: datetime


class TeamCreateSchema(BaseModel):
    """Create team schema."""

    name: str = Field(..., min_length=1, max_length=255)
    slug: str = Field(..., min_length=1, max_length=255, pattern=r"^[a-z0-9-]+$")
    description: str = ""


class TeamUpdateSchema(BaseModel):
    """Update team schema."""

    name: str | None = None
    description: str | None = None
