from django.db import models
from django.urls import reverse
from rekjrc.base_models import BaseModel, Ownable

ATTRIBUTE_NAMES = ["bearings","body","bumper_front","bumper_rear","camber_links",
                   "caster_blocks","chassis","control_arms","cooling","driveshafts",
                   "drive_type","esc","esc_motor","fuel","lights","motor",
                   "radio_system","rear_steer","rims","scale","sensor","servo",
                   "shocks","shocks_front","shocks_rear","transmission","wheel_hubs",
                   "wheels","wheels_front","wheels_rear"]

class Build(BaseModel, Ownable):
    year = models.PositiveIntegerField(blank=True, null=True)
    make = models.CharField(max_length=255, blank=True, null=True)
    model = models.CharField(max_length=255, blank=True, null=True)

    for attr in ATTRIBUTE_NAMES:
        locals()[attr] = models.CharField(max_length=255, blank=True, null=True, help_text=f"Enter {attr}")

    def __str__(self):
        return self.display_name

    def get_absolute_url(self):
            return reverse("builds:detail", kwargs={"uuid": self.uuid})

    class Meta:
        ordering = ["display_name"]
