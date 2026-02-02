from django.contrib import admin
from .models import Track

@admin.register(Track)
class TrackAdmin(admin.ModelAdmin):
    list_display = ("display_name", "location")
    search_fields = ("display_name", "location__display_name")
    list_filter = ("location",)
    ordering = ("display_name",)
