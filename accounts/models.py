from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.conf import settings
from rekjrc.base_models import BaseModel

class Follow(BaseModel):
    follower = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="followers")
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        related_name="followers")
    object_id = models.PositiveIntegerField()
    object = GenericForeignKey("content_type", "object_id")

    @property
    def followed_type(self):
        return self.content_type.model

    class Meta:
        unique_together = ("follower", "content_type", "object_id")

    def __str__(self):
        return f"{self.follower} follows {self.object}"

