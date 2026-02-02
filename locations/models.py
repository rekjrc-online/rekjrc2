from decimal import Decimal, ROUND_HALF_UP
from django.core.exceptions import ValidationError
from django.db import models
from rekjrc.base_models import BaseModel, Ownable
from django.urls import reverse

class Location(BaseModel, Ownable):
    address1 = models.CharField(max_length=255, blank=True, null=True)
    address2 = models.CharField(max_length=255, blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    state = models.CharField(max_length=20, blank=True, null=True)
    zip = models.CharField(max_length=20, blank=True, null=True)
    latitude = models.DecimalField(max_digits=9,decimal_places=6,null=True,blank=True)
    longitude = models.DecimalField(max_digits=9,decimal_places=6,null=True,blank=True)

    @property
    def has_advanced(self):
        return True

    class Meta:
        indexes = [models.Index(fields=["latitude", "longitude"])]

    def __str__(self):
        if self.latitude is not None and self.longitude is not None:
            return f"{self.display_name} ({self.latitude}, {self.longitude})"
        return self.display_name

    def get_absolute_url(self):
            return reverse("locations:detail", kwargs={"uuid": self.uuid})

    def clean_fields(self, exclude=None):
        if self.latitude is not None:
            self.latitude = Decimal(str(self.latitude)).quantize(
                Decimal("0.000001"),
                rounding=ROUND_HALF_UP,
            )
        if self.longitude is not None:
            self.longitude = Decimal(str(self.longitude)).quantize(
                Decimal("0.000001"),
                rounding=ROUND_HALF_UP,
            )
        super().clean_fields(exclude=exclude)

    def clean(self):
        super().clean()
        if self.latitude is not None:
            self.latitude = Decimal(str(self.latitude))
            if not (-90 <= self.latitude <= 90):
                raise ValidationError({"latitude": "Latitude must be between -90 and 90."})
            self.latitude = self.latitude.quantize(
                Decimal("0.000001"),
                rounding=ROUND_HALF_UP
            )
        if self.longitude is not None:
            self.longitude = Decimal(str(self.longitude))
            if not (-180 <= self.longitude <= 180):
                raise ValidationError({"longitude": "Longitude must be between -180 and 180."})
            self.longitude = self.longitude.quantize(
                Decimal("0.000001"),
                rounding=ROUND_HALF_UP
            )

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

class LocationTrack(BaseModel):
    location = models.ForeignKey(
        Location,
        on_delete=models.CASCADE,
        related_name="location_tracks")
    track = models.ForeignKey(
        "tracks.Track",
        on_delete=models.CASCADE,
        related_name="location_tracks")

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["location", "track"],
                name="unique_location_track" )]