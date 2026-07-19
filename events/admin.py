from django.contrib import admin
from .models import Event, EventLocation, EventTeam, EventClub, EventStore, EventRace, EventCheckin

class BaseEventInline(admin.TabularInline):
    extra = 0
    autocomplete_fields = ()
    show_change_link = True

class EventLocationInline(BaseEventInline):
    model = EventLocation
    autocomplete_fields = ("location",)

class EventTeamInline(BaseEventInline):
    model = EventTeam
    autocomplete_fields = ("team",)

class EventClubInline(BaseEventInline):
    model = EventClub
    autocomplete_fields = ("club",)

class EventStoreInline(BaseEventInline):
    model = EventStore
    autocomplete_fields = ("store",)

class EventRaceInline(BaseEventInline):
    model = EventRace
    autocomplete_fields = ("race",)

@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = (
        "display_name",
        "event_date",
        "event_time",
        "event_days",
        "staff_team",
        "is_active",
    )

    search_fields = (
        "display_name",
    )

    list_filter = (
        "event_date",
        "is_active",
    )

    autocomplete_fields = ("staff_team",)

    ordering = ("-event_date",)

    inlines = [
        EventLocationInline,
        EventTeamInline,
        EventClubInline,
        EventStoreInline,
        EventRaceInline,
    ]

@admin.register(EventCheckin)
class EventCheckinAdmin(admin.ModelAdmin):
    list_display = (
        "rfid_code",
        "user",
        "event",
        "checked_in_by",
        "created_at",
    )

    search_fields = (
        "rfid_code",
        "user__email",
        "user__first_name",
        "user__last_name",
    )

    list_filter = (
        "event",
    )

    autocomplete_fields = ("event", "user", "checked_in_by")

    ordering = ("-created_at",)
