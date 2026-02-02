from django.db import models
from django.contrib.auth.models import User
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.forms import ValidationError

class ChatMessage(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="chat_messages")
    channel_content_type = models.ForeignKey(
        ContentType,
        null=True,
        on_delete=models.CASCADE,
        related_name="chat_channel_messages")
    channel_object_id = models.PositiveIntegerField(null=True, blank=True)
    channel = GenericForeignKey("channel_content_type", "channel_object_id")
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]
        indexes = [
            models.Index(fields=["channel_content_type", "channel_object_id"]),
            models.Index(fields=["created_at"])]

    def __str__(self):
        return f"{self.speaker_display}: {self.content[:40]}"

    @property
    def speaker_display(self):
        full_name = f"{self.user.first_name} {self.user.last_name}".strip()
        return full_name or self.user.username

    def clean(self):
        if not self.user:
            raise ValidationError("User is required.")
        if not self.channel:
            raise ValidationError("Channel is required.")
