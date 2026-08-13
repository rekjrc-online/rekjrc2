from django.contrib import admin
from .models import Store

@admin.register(Store)
class StoreAdmin(admin.ModelAdmin):
    list_display = (
        "display_name", "owner", "location", "website", "email",
        "is_storefront_enabled", "can_accept_payments",
    )
    search_fields = ("display_name", "owner__username", "location__display_name")
    list_filter = ("location", "is_storefront_enabled")
    readonly_fields = ("slug",)
    ordering = ("display_name",)

    @admin.display(boolean=True, description="Stripe key in .env")
    def can_accept_payments(self, obj):
        return obj.can_accept_payments
