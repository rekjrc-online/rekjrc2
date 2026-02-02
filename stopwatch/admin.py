from django.contrib import admin
from .models import StopwatchRun

@admin.register(StopwatchRun)
class StopwatchRunAdmin(admin.ModelAdmin):
    list_display = ("race", "racedriver", "elapsed_time_display")
    search_fields = ("race__display_name", "racedriver__driver_name", "racedriver__model_name")
    list_filter = ("race",)
    ordering = ("race__created_at",)

    def elapsed_time_display(self, obj):
        if obj.elapsed_time is not None:
            return f"{obj.elapsed_time:.2f}s"
        return "No time recorded"
    elapsed_time_display.short_description = "Elapsed Time"
