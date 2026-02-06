from django.test import TestCase
from django.contrib.auth import get_user_model
from races.forms import RaceForm, RaceDriverForm
from races.models import Race
from clubs.models import Club
from events.models import Event
from locations.models import Location
from teams.models import Team
from tracks.models import Track
from stores.models import Store
from builds.models import Build
from drivers.models import Driver

User = get_user_model()

class RaceFormTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="tester", password="pass")
        self.club = Club.objects.create(display_name="Test Club", owner=self.user)
        self.location = Location.objects.create(display_name="Test Location", owner=self.user)
        self.event = Event.objects.create(display_name="Test Event", owner=self.user)
        self.track = Track.objects.create(display_name="Test Track", owner=self.user)
        self.team = Team.objects.create(display_name="Test Team", owner=self.user)
        self.store = Store.objects.create(display_name="Test Store", owner=self.user)

    def test_race_form_valid(self):
        form_data = {
            'display_name': 'My Race',
            'race_type': 'Lap Race',
            'event': self.event.pk,
            'location': self.location.pk,
            'track': self.track.pk,
            'club': self.club.pk,
            'team': self.team.pk,
            'store': self.store.pk,
            'transponder': 'LapMonitor',
            'entry_locked': True,
            'race_finished': False,
            'is_active': True
        }
        form = RaceForm(data=form_data)
        self.assertTrue(form.is_valid())
        race = form.save(commit=False)
        race.owner = self.user
        race.save()
        self.assertEqual(race.display_name, 'My Race')

    def test_race_form_invalid_missing_required(self):
        form = RaceForm(data={})
        self.assertFalse(form.is_valid())
        self.assertIn('display_name', form.errors)
        self.assertIn('race_type', form.errors)

class RaceDriverFormTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="driveruser", password="pass")
        self.race_owner = User.objects.create_user(username="raceowner", password="pass")
        self.race = Race.objects.create(display_name="Race1", owner=self.race_owner)
        self.build = Build.objects.create(display_name="Test Build", owner=self.user)
        self.driver = Driver.objects.create(display_name="Test Driver", owner=self.user)

    def test_race_driver_form_valid(self):
        form_data = {
            'race': self.race.pk,
            'user': self.user.pk,
            'build': self.build.pk,
            'driver': self.driver.pk,
            'transponder': 'LapMonitor',
            'is_active': True
        }
        form = RaceDriverForm(data=form_data)
        self.assertTrue(form.is_valid())
        driver = form.save(commit=False)
        driver.owner = self.user
        driver.save()
        self.assertEqual(driver.build, self.build)

    def test_race_driver_form_invalid_missing_required(self):
        form = RaceDriverForm(data={})
        self.assertFalse(form.is_valid())
        self.assertIn('race', form.errors)
        self.assertIn('user', form.errors)
