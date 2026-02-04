from django.contrib import admin
from django.utils.html import format_html
from .models import ShortURL

@admin.register(ShortURL)
class ShortURLAdmin(admin.ModelAdmin):
    list_display = (
        "code",
        "destination_link",
        "click_count",
        "active",
        "owner_display",
        "created_at",
    )

    list_filter = ("active", "created_at")
    search_fields = ("code", "destination_url")
    ordering = ("-created_at",)

    readonly_fields = ("created_at", "updated_at")

    fieldsets = (
        (
            None,
            {
                "fields": (
                    "code",
                    "destination_url",
                    "active",
                )
            },
        ),
        (
            "Ownership (optional)",
            {
                "fields": (
                    "owner_content_type",
                    "owner_object_id",
                ),
                "classes": ("collapse",),
            },
        ),
        (
            "Timestamps",
            {
                "fields": ("created_at", "updated_at"),
                "classes": ("collapse",),
            },
        ),
    )

    def destination_link(self, obj):
        return format_html(
            '<a href="{0}" target="_blank">{0}</a>',
            obj.destination_url,
        )

    destination_link.short_description = "Destination URL"

    def owner_display(self, obj):
        if obj.owner:
            return str(obj.owner)
        return "—"

    owner_display.short_description = "Owner"
