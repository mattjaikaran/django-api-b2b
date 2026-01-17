"""Admin configuration for organizations."""

from django.contrib import admin

from .models import Invitation, Membership, Organization, Team


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    """Organization admin."""

    list_display = ("name", "slug", "plan", "created_at")
    list_filter = ("plan", "created_at")
    search_fields = ("name", "slug")
    readonly_fields = ("id", "created_at", "updated_at")


@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    """Team admin."""

    list_display = ("name", "organization", "slug", "created_at")
    list_filter = ("organization", "created_at")
    search_fields = ("name", "slug", "organization__name")
    readonly_fields = ("id", "created_at", "updated_at")


@admin.register(Membership)
class MembershipAdmin(admin.ModelAdmin):
    """Membership admin."""

    list_display = ("user", "organization", "role", "is_active", "created_at")
    list_filter = ("role", "is_active", "organization")
    search_fields = ("user__email", "organization__name")
    readonly_fields = ("id", "created_at", "updated_at")


@admin.register(Invitation)
class InvitationAdmin(admin.ModelAdmin):
    """Invitation admin."""

    list_display = ("email", "organization", "role", "status", "expires_at")
    list_filter = ("status", "role", "organization")
    search_fields = ("email", "organization__name")
    readonly_fields = ("id", "token", "created_at")
