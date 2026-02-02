from django.contrib import admin
from .models import StripePaymentLog

@admin.register(StripePaymentLog)
class StripePaymentLogAdmin(admin.ModelAdmin):
    list_display = ("user", "product_slug", "amount_total", "currency", "status", "paid_at", "created_at")
    search_fields = ("user__username", "product_slug", "stripe_session_id", "stripe_payment_intent")
    list_filter = ("status", "currency", "created_at", "paid_at")
    readonly_fields = ("created_at",)
    ordering = ("-created_at",)
