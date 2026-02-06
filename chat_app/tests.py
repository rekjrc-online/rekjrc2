from django.test import TestCase
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from .models import ChatMessage
from .forms import ChatMessageForm

class ChatMessageModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="jason",password="password")
        self.other_user = User.objects.create_user(username="evil",password="password")
        self.channel = self.user

    def test_chat_message_creation(self):
        msg = ChatMessage.objects.create(
            user=self.user,
            channel_content_type=ContentType.objects.get_for_model(self.channel),
            channel_object_id=self.channel.pk,
            content="Hello world")
        self.assertEqual(msg.user, self.user)
        self.assertEqual(msg.channel, self.channel)
        self.assertEqual(msg.content, "Hello world")

    def test_speaker_display_user(self):
        msg = ChatMessage(
            user=self.user,
            channel=self.channel,
            content="Test")
        self.assertEqual(msg.speaker_display, "jason")

# ----------------------------------------------------------------------
# Form tests
# ----------------------------------------------------------------------
class ChatMessageFormTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="jason",
            password="password")
        self.other_user = User.objects.create_user(
            username="evil",
            password="password")
        self.channel = self.user

    def test_form_valid(self):
        form = ChatMessageForm(
            data={"content": "Hello chat"},
            user=self.user,
            channel=self.channel)
        self.assertTrue(form.is_valid())
        msg = form.save()
        self.assertEqual(msg.user, self.user)
        self.assertEqual(msg.channel, self.channel)
        self.assertEqual(msg.content, "Hello chat")

    def test_form_invalid_without_user(self):
        form = ChatMessageForm(
            data={"content": "Hello"},
            channel=self.channel)
        self.assertFalse(form.is_valid())
        self.assertIn("__all__", form.errors)

    def test_form_invalid_without_channel(self):
        form = ChatMessageForm(
            data={"content": "Hello"},
            user=self.user)
        self.assertFalse(form.is_valid())
        self.assertIn("__all__", form.errors)
