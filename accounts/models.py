from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from rekjrc.base_models import BaseModel
import qrcode

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    uuid = models.UUIDField(unique=True, editable=False, blank=True, null=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    avatar = models.ImageField(upload_to="avatars/", blank=True, null=True)
    is_verified = models.BooleanField(default=False)
    sms_opt_in = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.username} Profile"

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