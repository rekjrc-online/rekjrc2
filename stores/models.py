from django.db import models
from django.urls import reverse
from rekjrc.base_models import BaseModel, Ownable
from locations.models import Location

class Store(BaseModel, Ownable):
    location = models.ForeignKey (
        Location,
        on_delete=models.SET_NULL,
        related_name='stores',
        null=True,
        blank=True )
    description = models.TextField(blank=True, null=True)
    website = models.URLField(blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True)

    def __str__(self):
        return self.display_name

    def get_absolute_url(self):
            return reverse("stores:detail", kwargs={"uuid": self.uuid})
