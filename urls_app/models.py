from django.db import models
from django.conf import settings
from rekjrc.base_models import BaseModel

class ShortURL(BaseModel):
    code = models.CharField(max_length=20, unique=True)
    destination_url = models.URLField()
    active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.code} → {self.destination_url}"

class ClickEvent(BaseModel):
    short_url = models.ForeignKey(
        ShortURL,
        on_delete=models.CASCADE,
        related_name="click_events"
    )
    user_agent = models.TextField(blank=True, null=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)

    def __str__(self):
        return f"Click on {self.short_url.code} at {self.created_at:%Y-%m-%d %H:%M:%S}"
