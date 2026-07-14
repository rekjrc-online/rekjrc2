from django.contrib import admin
from .models import Device, DevicePayload, DeviceWhitelist


@admin.register(Device)
class DeviceAdmin(admin.ModelAdmin):
    list_display = (
        "name", "mac", "owner_display", "owner_type",
        "claimed_by", "description", "created_at", "updated_at",
    )
    search_fields = (
        "name", "mac", "description",
        "claimed_by__username", "claimed_by__email",
    )
    list_filter = ("content_type", "claimed_by")
    ordering = ("name",)
    readonly_fields = ("created_at", "updated_at")
    raw_id_fields = ("claimed_by", "content_type")

    @admin.display(description="Owner", ordering="object_id")
    def owner_display(self, obj):
        return obj.owner_display or "—"

    @admin.display(description="Owner type", ordering="content_type")
    def owner_type(self, obj):
        return obj.owner_type or "—"


@admin.register(DeviceWhitelist)
class DeviceWhitelistAdmin(admin.ModelAdmin):
    list_display = ("mac", "created_at")
    search_fields = ("mac",)
    ordering = ("mac",)
    readonly_fields = ("created_at",)


@admin.register(DevicePayload)
class DevicePayloadAdmin(admin.ModelAdmin):
    list_display = (
        "device", "created_at", "racedriver_id", "value",
        "name", "processed", "processed_at", "retry_count",
    )
    list_filter = ("processed", "device")
    search_fields = ("device__name", "device__mac", "value", "name")
    ordering = ("created_at",)
    readonly_fields = ("created_at", "processed_at")
    list_select_related = ("device",)
