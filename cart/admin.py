from django.contrib import admin

from .models import Cart, CartItem


class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ("uuid", "store", "user", "session_key", "checked_out", "item_count", "subtotal", "created_at")
    list_filter = ("checked_out", "store")
    search_fields = ("user__email", "session_key", "uuid", "store__display_name")
    inlines = [CartItemInline]
