"""Pydantic schemas for membership endpoints."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class MembershipSchema(BaseModel):
    """Membership response schema."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: int
    user_email: str
    organization_id: UUID
    organization_name: str
    role: str
    is_active: bool
    created_at: datetime


class MembershipCreateSchema(BaseModel):
    """Create membership (internal use)."""

    user_id: int
    organization_id: UUID
    role: str = "member"


class MembershipUpdateSchema(BaseModel):
    """Update membership schema."""

    role: str | None = None
    is_active: bool | None = None
