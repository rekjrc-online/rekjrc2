from django.contrib import admin, messages
from .models import (
    Device, DevicePayload, DeviceWhitelist, WebhookDelivery, WebhookEndpoint,
)


@admin.register(Device)
class DeviceAdmin(admin.ModelAdmin):
    list_display = (
        "name", "mac", "owner_display", "owner_type",
        "claimed_by", "webhook_enabled", "webhook_endpoint",
        "description", "created_at", "updated_at",
    )
    search_fields = (
        "name", "mac", "description",
        "claimed_by__username", "claimed_by__email",
    )
    list_filter = ("content_type", "claimed_by", "webhook_enabled")
    ordering = ("name",)
    readonly_fields = ("created_at", "updated_at")
    raw_id_fields = ("claimed_by", "content_type")
    autocomplete_fields = ("webhook_endpoint",)

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        ep = obj.webhook_endpoint
        if ep and obj.claimed_by_id and ep.account_id != obj.claimed_by_id:
            messages.warning(
                request,
                f"Webhook endpoint belongs to {ep.account}, but this device "
                f"was claimed by {obj.claimed_by}.")

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("webhook_endpoint")

    @admin.display(description="Owner", ordering="object_id")
    def owner_display(self, obj):
        return obj.owner_display or "—"

    @admin.display(description="Owner type", ordering="content_type")
    def owner_type(self, obj):
        return obj.owner_type or "—"


@admin.register(WebhookEndpoint)
class WebhookEndpointAdmin(admin.ModelAdmin):
    list_display = (
        "name", "url", "account", "is_active", "device_count",
        "consecutive_failures", "last_success_at", "last_failure_at",
    )
    list_filter = ("is_active",)
    search_fields = ("name", "url", "account__username", "account__email")
    raw_id_fields = ("account",)
    readonly_fields = (
        "uuid", "created_at", "updated_at", "consecutive_failures",
        "last_success_at", "last_failure_at",
    )

    @admin.display(description="Devices")
    def device_count(self, obj):
        return obj.devices.count()


@admin.register(WebhookDelivery)
class WebhookDeliveryAdmin(admin.ModelAdmin):
    list_display = (
        "id", "payload", "endpoint", "status", "attempts",
        "status_code", "error", "created_at", "delivered_at",
    )
    list_filter = ("status", "endpoint")
    list_select_related = ("payload__device", "endpoint")
    raw_id_fields = ("payload", "endpoint")
    readonly_fields = ("created_at", "delivered_at", "next_attempt_at")

    def has_add_permission(self, request):
        return False


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
