"""Pydantic schemas for organization endpoints."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


# Organization schemas
class OrganizationSchema(BaseModel):
    """Organization response schema."""

    id: UUID
    name: str
    slug: str
    logo_url: str | None = None
    website: str | None = None
    plan: str
    created_at: datetime

    class Config:
        from_attributes = True


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


# Team schemas
class TeamSchema(BaseModel):
    """Team response schema."""

    id: UUID
    organization_id: UUID
    name: str
    slug: str
    description: str
    created_at: datetime

    class Config:
        from_attributes = True


class TeamCreateSchema(BaseModel):
    """Create team schema."""

    name: str = Field(..., min_length=1, max_length=255)
    slug: str = Field(..., min_length=1, max_length=255, pattern=r"^[a-z0-9-]+$")
    description: str = ""


class TeamUpdateSchema(BaseModel):
    """Update team schema."""

    name: str | None = None
    description: str | None = None


# Membership schemas
class MembershipSchema(BaseModel):
    """Membership response schema."""

    id: UUID
    user_id: int
    user_email: str
    organization_id: UUID
    organization_name: str
    role: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class MembershipCreateSchema(BaseModel):
    """Create membership (internal use)."""

    user_id: int
    organization_id: UUID
    role: str = "member"


class MembershipUpdateSchema(BaseModel):
    """Update membership schema."""

    role: str | None = None
    is_active: bool | None = None


# Invitation schemas
class InvitationSchema(BaseModel):
    """Invitation response schema."""

    id: UUID
    organization_id: UUID
    organization_name: str
    email: EmailStr
    role: str
    status: str
    invited_by_email: str | None
    expires_at: datetime
    created_at: datetime

    class Config:
        from_attributes = True


class InvitationCreateSchema(BaseModel):
    """Create invitation schema."""

    email: EmailStr
    role: str = "member"


class InvitationAcceptSchema(BaseModel):
    """Accept invitation schema."""

    token: str


# Organization with membership info
class OrganizationWithRoleSchema(BaseModel):
    """Organization with user's role."""

    id: UUID
    name: str
    slug: str
    logo_url: str | None = None
    plan: str
    role: str  # User's role in this org
    is_active: bool

    class Config:
        from_attributes = True
