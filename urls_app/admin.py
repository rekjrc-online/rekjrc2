from django.contrib import admin
from .models import ShortURL, ClickEvent

@admin.register(ShortURL)
class ShortURLAdmin(admin.ModelAdmin):
    list_display = ("code", "destination_url", "active", "created_at")
    list_filter = ("active", "created_at")
    search_fields = ("code", "destination_url")
    ordering = ("-created_at",)

@admin.register(ClickEvent)
class ClickEventAdmin(admin.ModelAdmin):
    list_display = ("short_url", "ip_address", "user_agent", "created_at")
    search_fields = ("short_url__code", "ip_address", "user_agent")
    ordering = ("-created_at",)
