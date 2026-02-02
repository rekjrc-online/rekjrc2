from django.contrib import admin
from .models import LongJumpRun

@admin.register(LongJumpRun)
class LongJumpRunAdmin(admin.ModelAdmin):
    list_display = ("race_display", "racedriver_display", "feet", "inches", "total_inches")
    search_fields = ("race__profile__display_name", "racedriver__driver__display_name")
    list_filter = ("race",)
    ordering = ("race__created_at",)

    def race_display(self, obj):
        return str(obj.race)
    race_display.short_description = "Race"

    def racedriver_display(self, obj):
        return str(obj.racedriver)
    racedriver_display.short_description = "Driver"

    def total_inches(self, obj):
        return obj.total_inches
    total_inches.short_description = "Total Inches"
