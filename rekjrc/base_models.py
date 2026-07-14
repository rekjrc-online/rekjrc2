from django.conf import settings
from django.db import models
import uuid

class BaseModel(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

class Ownable(models.Model):
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
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
        if self.avatar:
            from rekjrc.tasks import resize_avatar
            resize_avatar.delay(
                self._meta.app_label,
                self._meta.model_name,
                self.pk,
            )