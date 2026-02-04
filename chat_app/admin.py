from django.contrib import admin
from .models import ChatMessage

@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ("content_preview", "user", "channel_display", "created_at")
    search_fields = ("content", "user__username")
    list_filter = ("created_at",)
    ordering = ("-created_at",)

    def content_preview(self, obj):
        return obj.content[:50]
    content_preview.short_description = "Content"

    def channel_display(self, obj):
        if obj.channel is None:
            return "-"
        return str(obj.channel)
    channel_display.short_description = "Channel"
