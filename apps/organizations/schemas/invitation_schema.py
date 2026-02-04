"""Pydantic schemas for invitation endpoints."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr


class InvitationSchema(BaseModel):
    """Invitation response schema."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    organization_id: UUID
    organization_name: str
    email: EmailStr
    role: str
    status: str
    invited_by_email: str | None
    expires_at: datetime
    created_at: datetime


class InvitationCreateSchema(BaseModel):
    """Create invitation schema."""

    email: EmailStr
    role: str = "member"


class InvitationAcceptSchema(BaseModel):
    """Accept invitation schema."""

    token: str
