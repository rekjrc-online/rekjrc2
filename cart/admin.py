from django.contrib import admin

from .models import Cart, CartItem, PromoCode


class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ("uuid", "store", "user", "session_key", "checked_out", "item_count", "subtotal", "promo_code", "created_at")
    list_filter = ("checked_out", "store")
    search_fields = ("user__email", "session_key", "uuid", "store__display_name")
    inlines = [CartItemInline]


@admin.register(PromoCode)
class PromoCodeAdmin(admin.ModelAdmin):
    list_display = ("code", "discount_percent", "store", "is_active", "expires_at", "times_used", "max_uses", "created_at")
    list_filter = ("is_active", "store")
    search_fields = ("code", "description")
    readonly_fields = ("times_used", "created_at", "updated_at")
