from django.contrib import admin
from .models import Team, TeamMember

@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ("display_name",)
    search_fields = ("display_name",)
    readonly_fields = ("created_at", "updated_at")
    ordering = ("display_name",)

@admin.register(TeamMember)
class TeamMemberAdmin(admin.ModelAdmin):
    list_display = ("team", "user")
    search_fields = ("team__display_name", "user__username")
    list_filter = ("team",)
    ordering = ("team", "user")
