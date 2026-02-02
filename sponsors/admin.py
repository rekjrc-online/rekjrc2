from django.contrib import admin
from .models import Sponsor, SponsorClick

class SponsorClickInline(admin.TabularInline):
    model = SponsorClick
    extra = 0
    readonly_fields = ("user", "ip_address", "user_agent", "created_at")
    can_delete = False

@admin.register(Sponsor)
class SponsorAdmin(admin.ModelAdmin):
    list_display = ("name", "website", "clicks_count")
    search_fields = ("name", "website")
    inlines = [SponsorClickInline]

    def clicks_count(self, obj):
        return obj.clicks.count()
    clicks_count.short_description = "Clicks"

@admin.register(SponsorClick)
class SponsorClickAdmin(admin.ModelAdmin):
    list_display = ("sponsor", "user", "ip_address", "created_at")
    search_fields = ("sponsor__name", "user__username", "ip_address")
    list_filter = ("sponsor",)
    ordering = ("-created_at",)