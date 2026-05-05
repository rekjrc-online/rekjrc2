from django.contrib import admin
from .models import Device, DevicePayload

@admin.register(Device)
class DeviceAdmin(admin.ModelAdmin):
    list_display  = ("name", "mac", "owner_user", "owner_team", "description", "created_at", "updated_at")
    search_fields = ("name", "mac", "description", "owner_user__username", "owner_team__display_name")
    list_filter   = ("owner_team",)
    ordering      = ("name",)
    readonly_fields = ("created_at", "updated_at")

@admin.register(DevicePayload)
class DevicePayloadAdmin(admin.ModelAdmin):
    list_display   = ("device", "created_at", "racedriver_id", "value",
                       "name", "processed", "processed_at", "retry_count")
    list_filter    = ("processed", "device")
    search_fields  = ("device__name", "device__mac", "value", "name")
    ordering       = ("created_at",)
    readonly_fields = ("created_at", "processed_at")
    list_select_related = ("device",)
