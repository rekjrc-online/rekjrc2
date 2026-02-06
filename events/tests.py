from django.test import TestCase
from django.contrib.auth.models import User
from .models import Event
from .forms import EventForm
from datetime import date, time

class EventModelFormTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="user1", password="pass")

    def test_event_str(self):
        event = Event.objects.create(owner=self.user, display_name="Race Day")
        expected_str = f"{event.event_date.strftime('%a %m/%d/%y')} - Race Day"
        self.assertEqual(str(event), expected_str)

    def test_event_form_valid(self):
        form_data = {
            'display_name': 'Fun Event',
            'event_date': date.today(),
            'event_time': time(hour=10, minute=30),
            'event_days': 2,
            'is_active': True }
        form = EventForm(data=form_data)
        self.assertTrue(form.is_valid())
        event = form.save(commit=False)
        event.owner = self.user
        event.save()
        self.assertEqual(event.display_name, 'Fun Event')
        self.assertTrue(event.is_active)
        self.assertEqual(event.event_days, 2)

    def test_event_form_invalid_days(self):
        form_data = {
            'display_name': 'Bad Event',
            'event_date': date.today(),
            'event_time': time(hour=10, minute=30),
            'event_days': 0,  # invalid
            'is_active': True,
        }
        form = EventForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('event_days', form.errors)
