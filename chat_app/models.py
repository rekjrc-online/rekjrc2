from django.db import models
from django.contrib.auth.models import User
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError  # use this one

class ChatMessage(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="chat_messages")
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    channel = GenericForeignKey("channel_content_type", "channel_object_id")
    channel_object_id = models.PositiveIntegerField(null=True, blank=True)
    channel_content_type = models.ForeignKey(
        ContentType,
        null=True,
        on_delete=models.CASCADE,
        related_name="chat_channel_messages"
    )

    class Meta:
        ordering = ["created_at"]
        indexes = [
            models.Index(fields=["channel_content_type", "channel_object_id"]),
            models.Index(fields=["created_at"])
        ]

    def __str__(self):
        return f"{self.user}: {self.content[:40]}"

    @property
    def speaker_display(self):
        full_name = f"{self.user}".strip()
        return full_name or self.user.username

    def clean(self):
        # Only validate if fields exist
        errors = {}
        if not getattr(self, "user", None):
            errors["user"] = "User is required."
        if not (getattr(self, "channel_object_id", None) and getattr(self, "channel_content_type", None)):
            errors["channel"] = "Channel is required."
        if errors:
            raise ValidationError(errors)
