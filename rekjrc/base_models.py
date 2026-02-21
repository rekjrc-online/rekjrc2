from PIL import Image
import uuid
from django.conf import settings
from django.db import models


class BaseModel(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Ownable(models.Model):
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,  # string ref avoids AppRegistryNotReady on startup
        on_delete=models.CASCADE,
        related_name="%(class)s_owned")
    display_name = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    allow_followers = models.BooleanField(default=True)
    enable_chat = models.BooleanField(default=False)

    class Meta:
        abstract = True

    @property
    def follower_count(self):
        return self.followers.count()

    @property
    def display_with_type(self):
        return self._meta.verbose_name.title() + ' - ' + self.display_name

    def deactivate(self):
        self.is_active = False
        self.save(update_fields=["is_active"])

    def activate(self):
        self.is_active = True
        self.save(update_fields=["is_active"])

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.avatar and hasattr(self.avatar, "path"):
            try:
                img = Image.open(self.avatar.path)
                img.thumbnail((300, 300))
                img.save(self.avatar.path, optimize=True, quality=85)
            except Exception as e:
                print("Avatar resize failed:", e)