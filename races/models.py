from django.db import models
from django.conf import settings
from django.urls import reverse
from rekjrc.base_models import BaseModel, Ownable
from clubs.models import Club
from events.models import Event
from locations.models import Location
from teams.models import Team
from tracks.models import Track
from stores.models import Store

class Race(BaseModel, Ownable):
    RACE_TYPE_CHOICES = [
        ('Lap Race',        'Lap Race'),
        ('Drag Race',       'Drag Race'),
        ('Crawler Comp',    'Crawler Comp'),
        ('Stopwatch Race',  'Stopwatch Race'),
        ('Long Jump',       'Long Jump'),
        ('Top Speed',       'Top Speed'),
        ('Judged Event',    'Judged Event'),
    ]
    race_type = models.CharField(
        max_length=30,
        choices=RACE_TYPE_CHOICES,
        default='Lap Race',
    )
    event = models.ForeignKey(
        Event,
        on_delete=models.SET_NULL,
        related_name='races',
        null=True,
        blank=True,
    )
    location = models.ForeignKey(
        Location,
        on_delete=models.SET_NULL,
        related_name='races',
        null=True,
        blank=True,
    )
    track = models.ForeignKey(
        Track,
        on_delete=models.SET_NULL,
        related_name='races',
        null=True,
        blank=True,
    )
    club = models.ForeignKey(
        Club,
        on_delete=models.SET_NULL,
        related_name='races',
        null=True,
        blank=True,
    )
    team = models.ForeignKey(
        Team,
        on_delete=models.SET_NULL,
        related_name='races',
        null=True,
        blank=True,
    )
    store = models.ForeignKey(
        Store,
        on_delete=models.SET_NULL,
        related_name='races',
        null=True,
        blank=True,
    )
    TRANSPONDER_CHOICES = [
        ('LapMonitor','LapMonitor'),
        ('MyLaps','MyLaps'),
    ]
    transponder = models.CharField(max_length=10, choices=TRANSPONDER_CHOICES, blank=True, null=True)
    entry_locked = models.BooleanField(default=False)
    race_finished = models.BooleanField(default=False)

    def __str__(self):
        return self.display_name

    def get_absolute_url(self):
        return reverse("races:detail", kwargs={"uuid": self.uuid})

class RaceDriver(BaseModel):
    race = models.ForeignKey(
        Race,
        on_delete=models.CASCADE,
        related_name='race_drivers')
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='race_drivers')
    build = models.ForeignKey(
        "builds.Build",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="race_entries")
    driver = models.ForeignKey(
        "drivers.Driver",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="race_entries")
    transponder = models.CharField(
        max_length=10,
        choices=[
            ('LapMonitor','LapMonitor'),
            ('MyLaps','MyLaps')],
        blank=True,
        null=True)
    finish_position = models.PositiveIntegerField(
        null=True,
        blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['race', 'driver', 'build'],
                name='unique_race_driver_build')]

    def __str__(self):
        return f"Driver: {self.driver or '-driver-'} - Build: {self.build or '-build-'}"
