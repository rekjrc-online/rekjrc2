from django.contrib import admin
from .models import JudgedScore


@admin.register(JudgedScore)
class JudgedScoreAdmin(admin.ModelAdmin):
    list_display = ("race", "racedriver", "judge", "score")
    search_fields = (
        "race__id",
        "racedriver__driver__display_name",
        "judge__username",
    )
    list_filter = ("race", "judge")
    ordering = ("race__created_at",)