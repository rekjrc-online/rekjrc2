from django.db import models
from django.urls import reverse
from rekjrc.base_models import BaseModel, Ownable
from locations.models import Location

class Track(BaseModel, Ownable):
    location = models.ForeignKey(
        Location,
        on_delete=models.CASCADE,
        related_name='tracks',
        null=True,
        blank=True,
    )

    def __str__(self):
        return self.display_name

    def get_absolute_url(self):
        return reverse("tracks:detail", kwargs={"uuid": self.uuid})
