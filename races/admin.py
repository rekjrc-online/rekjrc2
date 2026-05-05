from django.contrib import admin
from .models import Race, RaceDriver, RaceJudgeDevice

class RaceDriverInline(admin.TabularInline):
    model = RaceDriver
    extra = 0
    readonly_fields = ("user", "driver", "build", "transponder")

class RaceJudgeDeviceInline(admin.TabularInline):
    model = RaceJudgeDevice
    extra = 1

@admin.register(Race)
class RaceAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "race_type",
        "event",
        "location",
        "track",
        "club",
        "team",
        "store",
        "device",
        "entry_locked",
        "race_finished",
    )
    list_filter = ("race_type", "entry_locked", "race_finished", "event", "location", "track")
    search_fields = ("display", "race_type")
    ordering = ("-created_at",)
    inlines = [RaceDriverInline, RaceJudgeDeviceInline]

@admin.register(RaceDriver)
class RaceDriverAdmin(admin.ModelAdmin):
    list_display = ("race", "driver", "build", "user", "transponder")
    search_fields = ("driver", "build", "user__username")
    list_filter = ("race",)
    ordering = ("race__created_at",)

@admin.register(RaceJudgeDevice)
class RaceJudgeDeviceAdmin(admin.ModelAdmin):
    list_display = ("race", "judge", "device")
    list_filter = ("race",)
    search_fields = ("judge__username", "device__name", "device__mac")
