from django.test import TestCase
from django.core.exceptions import ValidationError
from .models import Location
from .forms import LocationForm
from django.contrib.auth import get_user_model

User = get_user_model()

class LocationModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="tester", password="pass")

    def test_create_location_valid(self):
        loc = Location.objects.create(
            display_name="Test Track",
            latitude=45.123456,
            longitude=-73.654321,
            owner=self.user,
            is_active=True
        )
        self.assertEqual(str(loc), "Test Track (45.123456, -73.654321)")
        self.assertTrue(loc.is_active)

    def test_invalid_latitude_raises(self):
        loc = Location(
            display_name="Invalid Latitude",
            latitude=100,  # invalid
            longitude=0,
            owner=self.user
        )
        with self.assertRaises(ValidationError) as cm:
            loc.full_clean()
        self.assertIn("latitude", cm.exception.message_dict)

    def test_invalid_longitude_raises(self):
        loc = Location(
            display_name="Invalid Longitude",
            latitude=0,
            longitude=200,  # invalid
            owner=self.user
        )
        with self.assertRaises(ValidationError) as cm:
            loc.full_clean()
        self.assertIn("longitude", cm.exception.message_dict)

class LocationFormTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="tester", password="pass")

    def test_form_valid_data(self):
        form_data = {
            "display_name": "Form Track",
            "latitude": 40.123456,
            "longitude": -70.654321,
            "is_active": True
        }
        form = LocationForm(data=form_data)
        self.assertTrue(form.is_valid())
        loc = form.save(commit=False)
        loc.owner = self.user
        loc.save()
        self.assertEqual(Location.objects.count(), 1)
        self.assertEqual(str(loc), "Form Track (40.123456, -70.654321)")

    def test_form_invalid_latitude(self):
        form_data = {
            "display_name": "Bad Track",
            "latitude": 91,  # invalid
            "longitude": 0,
            "is_active": True
        }
        form = LocationForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn("latitude", form.errors)
