from django.contrib import admin
from .models import Race, RaceClass, RaceDriver, RaceJudgeDevice

class RaceClassInline(admin.TabularInline):
    model = RaceClass
    extra = 1
    fields = ("name",)

class RaceDriverInline(admin.TabularInline):
    model = RaceDriver
    extra = 0
    readonly_fields = ("user", "driver", "build", "transponder")

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        # Limit the class dropdown to the classes of the race being edited.
        if db_field.name == "race_class":
            race_id = request.resolver_match.kwargs.get("object_id") if request.resolver_match else None
            kwargs["queryset"] = RaceClass.objects.filter(race_id=race_id) if race_id else RaceClass.objects.none()
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

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
        "device",
        "entry_locked",
        "race_finished",
    )
    list_filter = ("race_type", "entry_locked", "race_finished", "event", "location", "track")
    search_fields = ("display", "race_type")
    ordering = ("-created_at",)
    inlines = [RaceClassInline, RaceDriverInline, RaceJudgeDeviceInline]

@admin.register(RaceClass)
class RaceClassAdmin(admin.ModelAdmin):
    list_display = ("name", "race")
    list_filter = ("race",)
    search_fields = ("name", "race__display_name")

@admin.register(RaceDriver)
class RaceDriverAdmin(admin.ModelAdmin):
    list_display = ("race", "race_class", "driver", "build", "user", "transponder")
    search_fields = ("driver", "build", "user__username")
    list_filter = ("race", "race_class")
    ordering = ("race__created_at",)

@admin.register(RaceJudgeDevice)
class RaceJudgeDeviceAdmin(admin.ModelAdmin):
    list_display = ("race", "judge", "device")
    list_filter = ("race",)
    search_fields = ("judge__username", "device__name", "device__mac")
