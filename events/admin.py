from django.contrib import admin
from .models import Event, EventLocation, EventTeam, EventClub, EventStore, EventRace

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
        "is_active",
    )

    search_fields = (
        "display_name",
    )

    list_filter = (
        "event_date",
        "is_active",
    )

    ordering = ("-event_date",)

    inlines = [
        EventLocationInline,
        EventTeamInline,
        EventClubInline,
        EventStoreInline,
        EventRaceInline,
    ]
