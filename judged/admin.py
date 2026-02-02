from django.contrib import admin
from drivers import models
from .models import JudgedEventRun, JudgedEventRunScore, Judge

class JudgedEventRunScoreInline(admin.TabularInline):
    model = JudgedEventRunScore
    extra = 1
    fields = ("judge", "score")
    readonly_fields = ()

@admin.register(JudgedEventRun)
class JudgedEventRunAdmin(admin.ModelAdmin):
    list_display = ("race_display", "racedriver_display", "average_score")
    search_fields = ("race__profile__display_name", "racedriver__driver__display_name")
    list_filter = ("race",)
    ordering = ("race__created_at",)
    inlines = [JudgedEventRunScoreInline]

    def race_display(self, obj):
        return str(obj.race)
    race_display.short_description = "Race"

    def racedriver_display(self, obj):
        return str(obj.racedriver)
    racedriver_display.short_description = "Driver"

    def average_score(self, obj):
        if obj.scores.exists():
            return round(obj.scores.aggregate(models.Avg("score"))["score__avg"], 1)
        return "-"
    average_score.short_description = "Average Score"

@admin.register(JudgedEventRunScore)
class JudgedEventRunScoreAdmin(admin.ModelAdmin):
    list_display = ("run_display", "judge", "score")
    search_fields = ("run__racedriver__driver__display_name", "judge__username")
    list_filter = ("run__race",)
    ordering = ("run__race__created_at",)

    def run_display(self, obj):
        return f"{obj.run.racedriver} - {obj.run.race}"
    run_display.short_description = "Run"

@admin.register(Judge)
class JudgeAdmin(admin.ModelAdmin):
    list_display = ("race_display", "user")
    search_fields = ("race__profile__display_name", "user__username")
    list_filter = ("race",)
    ordering = ("race__created_at",)

    def race_display(self, obj):
        return str(obj.race)
    race_display.short_description = "Race"
