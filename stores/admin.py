from django.contrib import admin
from .models import Store

@admin.register(Store)
class StoreAdmin(admin.ModelAdmin):
    list_display = ("display_name", "owner", "location", "website", "email")
    search_fields = ("display_name", "owner__username", "location__display_name")
    list_filter = ("location",)
    readonly_fields = ()
    ordering = ("display_name",)
