from django.conf import settings
from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator
from rekjrc.base_models import BaseModel, Ownable
from locations.models import Location
from django.urls import reverse

class Event(BaseModel, Ownable):
    event_date = models.DateField(default=timezone.now)
    event_time = models.TimeField(default=timezone.now)
    event_days = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1)])
    # The Team allowed to run check-in / other staff functions for this
    # event -- see events.views._event_staff_queryset(). Deliberately NOT
    # EventTeam: that's an unrelated many-to-many list (managed on the
    # Advanced page) of teams associated with the event in some other
    # sense (e.g. participating/sponsoring), and using it to also mean
    # "these people are staff" was a mistake -- this field is the actual
    # access-control concept. A plain FK, not OneToOneField: the same Team
    # can staff more than one Event over time, same shape as
    # races.Race.team/judge_team.
    staff_team = models.ForeignKey(
        "teams.Team",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="staffed_events")

    @property
    def has_advanced(self):
        return True

    def __str__(self):
        return f"{self.event_date.strftime('%a %m/%d/%y')} - {self.display_name}"

    def get_absolute_url(self):
        return reverse("events:detail", kwargs={"uuid": self.uuid})

class EventRace(BaseModel):
    event = models.ForeignKey(
        Event,
        on_delete=models.CASCADE,
        related_name="event_races")
    race = models.ForeignKey(
        "races.Race",
        on_delete=models.CASCADE,
        related_name="event_races")

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["event", "race"],
                name="unique_event_race" )]

class EventTeam(BaseModel):
    event = models.ForeignKey(
        Event,
        on_delete=models.CASCADE,
        related_name="event_teams")
    team = models.ForeignKey(
        "teams.Team",
        on_delete=models.CASCADE,
        related_name="event_teams")

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["event", "team"],
                name="unique_event_team")]

class EventClub(BaseModel):
    event = models.ForeignKey(
        Event,
        on_delete=models.CASCADE,
        related_name="event_clubs")
    club = models.ForeignKey(
        "clubs.Club",
        on_delete=models.CASCADE,
        related_name="event_clubs")

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["event", "club"],
                name="unique_event_club" )]

class EventStore(BaseModel):
    event = models.ForeignKey(
        Event,
        on_delete=models.CASCADE,
        related_name="event_stores")
    store = models.ForeignKey(
        "stores.Store",
        on_delete=models.CASCADE,
        related_name="event_stores")

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["event", "store"],
                name="unique_event_store" )]

class EventLocation(BaseModel):
    event = models.ForeignKey(
        Event,
        on_delete=models.CASCADE,
        related_name="event_locations")
    location = models.ForeignKey(
        Location,
        on_delete=models.CASCADE,
        related_name="event_locations")

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["event", "location"],
                name="unique_event_location" )]

class EventCheckin(BaseModel):
    """
    Associates a physical RFID lanyard code with a participant's account for
    ONE event. Cards are reused hardware -- the same physical card is meant
    to be re-linked to a different account at the next event -- so it's the
    (event, rfid_code) pair, not the code alone, that identifies "who is
    this." Re-scanning a code already checked in for this event (lost /
    reissued lanyard, or handed to someone else the same day) is expected to
    just re-point it rather than error -- see events.views.Checkin_, which
    does an update_or_create keyed on (event, rfid_code).

    Consumed directly by the Go gateway (rekjrc_ingest) via raw SQL against
    this table -- see Go/racedrivers.go / Go/db.go RaceDriverListForRfid()/
    RfidCheckin() -- to resolve a scanned card to the participant's own
    RaceDriver entries for whichever race a device is currently working.
    """
    event = models.ForeignKey(
        Event,
        on_delete=models.CASCADE,
        related_name="checkins")
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="event_checkins")
    rfid_code = models.CharField(max_length=64)
    checked_in_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="checkins_performed")

    class Meta:
        # No separate Index needed: the UniqueConstraint below already gives
        # Postgres a unique index covering (event, rfid_code), which serves
        # the equality lookups both the checkin view and the Go gateway do.
        constraints = [
            models.UniqueConstraint(
                fields=["event", "rfid_code"],
                name="unique_event_rfid_code")]
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.rfid_code} -> {self.user} @ {self.event}"
