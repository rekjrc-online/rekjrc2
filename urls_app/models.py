from django.db import models
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from rekjrc.base_models import BaseModel

class ShortURL(BaseModel):
    code = models.CharField(max_length=20, unique=True)
    destination_url = models.URLField()
    active = models.BooleanField(default=True)
    click_count = models.PositiveIntegerField(default=0)

    owner = GenericForeignKey("owner_content_type", "owner_object_id")
    owner_object_id = models.PositiveIntegerField(null=True, blank=True)
    owner_content_type = models.ForeignKey(ContentType, null=True, on_delete=models.CASCADE, related_name="urls")

    def __str__(self):
        return f"{self.code} → {self.destination_url}"