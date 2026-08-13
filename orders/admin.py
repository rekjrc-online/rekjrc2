from django.contrib import admin

from .models import Order, OrderItem


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ("variant", "product_name", "variant_name", "sku", "unit_price", "quantity", "line_total")
    can_delete = False


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        "uuid", "store", "email", "status", "subtotal", "shipping_cost",
        "total", "paid_at", "created_at",
    )
    list_filter = ("status", "store")
    search_fields = ("email", "uuid", "store__display_name", "stripe_checkout_session_id", "stripe_payment_intent")
    readonly_fields = (
        "store", "user", "email", "subtotal", "total",
        "stripe_checkout_session_id", "stripe_payment_intent", "paid_at", "created_at", "updated_at",
    )
    ordering = ("-created_at",)
    inlines = [OrderItemInline]
