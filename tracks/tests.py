from django.test import TestCase
from django.contrib.auth import get_user_model
from locations.models import Location
from tracks.models import Track
from tracks.forms import TrackForm

User = get_user_model()

class TrackTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="owner", password="pass")
        self.location = Location.objects.create(display_name="Test Location", owner=self.user)

    def test_track_str(self):
        track = Track.objects.create(display_name="Test Track", owner=self.user, location=self.location)
        self.assertEqual(str(track), "Test Track")

    def test_track_form_valid(self):
        form_data = {
            'display_name': "Form Track",
            'owner': self.user.pk,
            'location': self.location.pk,
            'is_active': True
        }
        form = TrackForm(data=form_data)
        self.assertTrue(form.is_valid())
        track = form.save()
        self.assertEqual(track.display_name, "Form Track")
        self.assertEqual(track.owner, self.user)
        self.assertEqual(track.location, self.location)
        self.assertTrue(track.is_active)

    def test_track_form_missing_location(self):
        form_data = {
            'display_name': "Invalid Track",
            'owner': self.user.pk,
            'is_active': True
        }
        form = TrackForm(data=form_data)
        self.assertTrue(form.is_valid())
