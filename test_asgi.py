import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.routing import ProtocolTypeRouter, URLRouter
from django.conf import settings
from django.urls import re_path
import django
import os

# ------------------------------
# Minimal Django setup
# ------------------------------
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "rekjrc.settings")
django.setup()

# ------------------------------
# WebSocket consumer
# ------------------------------
class TestChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = "test_room"
        self.room_group_name = f"chat_{self.room_name}"

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()
        await self.send(text_data=json.dumps({"message": "Connected!"}))

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data)
        msg = data.get("message", "")
        # Echo the message to the same group
        await self.channel_layer.group_send(
            self.room_group_name,
            {"type": "chat.message", "message": msg},
        )

    async def chat_message(self, event):
        await self.send(text_data=json.dumps({"message": event["message"]}))

# ------------------------------
# Routing
# ------------------------------
websocket_urlpatterns = [
    re_path(r"ws/test/$", TestChatConsumer.as_asgi()),
]

# ------------------------------
# ASGI app
# ------------------------------
from channels.layers import get_channel_layer
from channels.routing import URLRouter
from channels.sessions import SessionMiddlewareStack

from channels.auth import AuthMiddlewareStack

app = ProtocolTypeRouter({
    "websocket": AuthMiddlewareStack(
        URLRouter(websocket_urlpatterns)
    )
})
