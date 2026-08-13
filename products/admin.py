from django.contrib import admin

from .models import Product, ProductImage, ProductVariant


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1


class ProductVariantInline(admin.TabularInline):
    model = ProductVariant
    extra = 1
    fields = ("name", "sku", "price_override", "is_active", "sort_order")


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "store", "base_price", "is_active", "sort_order", "created_at")
    list_filter = ("is_active", "store")
    search_fields = ("name", "slug", "description", "store__display_name", "variants__sku")
    prepopulated_fields = {"slug": ("name",)}
    ordering = ("store", "sort_order", "name")
    # thumbnail is auto-generated from the first Product image (see
    # rekjrc.tasks.resize_product_thumbnail) -- not something to hand-upload.
    readonly_fields = ("thumbnail",)
    inlines = [ProductImageInline, ProductVariantInline]


@admin.register(ProductVariant)
class ProductVariantAdmin(admin.ModelAdmin):
    list_display = ("product", "name", "sku", "price", "is_active")
    list_filter = ("is_active", "product__store")
    search_fields = ("sku", "name", "product__name", "product__store__display_name")
