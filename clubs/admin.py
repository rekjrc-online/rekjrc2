from django.contrib import admin
from .models import Club, ClubLocation, ClubMember

@admin.register(Club)
class ClubAdmin(admin.ModelAdmin):
    list_display = ("display_name", "owner")
    search_fields = ("display_name", "owner__username")
    ordering = ("display_name",)

@admin.register(ClubLocation)
class ClubLocationAdmin(admin.ModelAdmin):
    list_display = ("club_display", "location")
    search_fields = ("club__display_name", "location__display_name")
    list_filter = ("club", "location")
    ordering = ("club__display_name",)

    def club_display(self, obj):
        return obj.club.display_name

    club_display.short_description = "Club"

@admin.register(ClubMember)
class ClubMemberAdmin(admin.ModelAdmin):
    list_display = ("user", "club_display", "role")
    search_fields = ("user__username", "club__display_name", "role")
    list_filter = ("club",)
    ordering = ("club__display_name", "user__username")

    def club_display(self, obj):
        return obj.club.display_name

    club_display.short_description = "Club"
