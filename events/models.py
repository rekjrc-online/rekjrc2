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
