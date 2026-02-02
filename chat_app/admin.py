from django.contrib import admin
from .models import ChatMessage

@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ("content_preview", "user", "speaker_display", "channel_display", "created_at")
    search_fields = ("content", "user__username")
    list_filter = ("created_at",)
    ordering = ("-created_at",)

    def content_preview(self, obj):
        return obj.content[:50]
    content_preview.short_description = "Content"

    def speaker_display(self, obj):
        return obj.speaker_display
    speaker_display.short_description = "Speaker"

    def channel_display(self, obj):
        if obj.channel is None:
            return "-"
        return str(obj.channel)
    channel_display.short_description = "Channel"
