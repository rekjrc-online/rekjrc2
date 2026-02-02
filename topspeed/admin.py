from django.contrib import admin
from .models import TopSpeedRun

@admin.register(TopSpeedRun)
class TopSpeedRunAdmin(admin.ModelAdmin):
    list_display = ("racedriver", "race", "topspeed")
    search_fields = ("racedriver__driver_name", "racedriver__model_name", "race__display_name")
    list_filter = ("race",)
    ordering = ("race", "racedriver")
