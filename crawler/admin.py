from django.contrib import admin
from .models import CrawlerRun, CrawlerRunLog

class CrawlerRunLogInline(admin.TabularInline):
    model = CrawlerRunLog
    extra = 1
    fields = ("milliseconds", "label", "delta")
    readonly_fields = ()
    ordering = ("milliseconds",)

@admin.register(CrawlerRun)
class CrawlerRunAdmin(admin.ModelAdmin):
    list_display = ("race_display", "racedriver_display", "elapsed_time", "penalty_points", "total_log_points")
    search_fields = ("race__profile__display_name", "racedriver__driver__display_name")
    list_filter = ("race",)
    ordering = ("race__created_at",)

    inlines = [CrawlerRunLogInline]

    def race_display(self, obj):
        return obj.race.__str__()
    race_display.short_description = "Race"

    def racedriver_display(self, obj):
        return obj.racedriver.__str__()
    racedriver_display.short_description = "Driver"

    def total_log_points(self, obj):
        return obj.total_log_points()
    total_log_points.short_description = "Total Log Points"

@admin.register(CrawlerRunLog)
class CrawlerRunLogAdmin(admin.ModelAdmin):
    list_display = ("run_display", "milliseconds", "label", "delta")
    search_fields = ("run__racedriver__driver__display_name", "label")
    ordering = ("run__race__created_at", "milliseconds")

    def run_display(self, obj):
        return f"{obj.run.racedriver} - {obj.run.race}"
    run_display.short_description = "Run"
