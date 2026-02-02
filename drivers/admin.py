from django.contrib import admin
from .models import Driver

@admin.register(Driver)
class DriverAdmin(admin.ModelAdmin):
    list_display = ("display_name", "owner")
    search_fields = ("display_name", "owner__username")
    ordering = ("display_name",)
