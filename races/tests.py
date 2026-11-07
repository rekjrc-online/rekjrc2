from django.test import TestCase
from django.contrib.auth import get_user_model
from races.forms import RaceForm, RaceDriverForm
from races.models import Race
from events.models import Event
from locations.models import Location
from tracks.models import Track
from builds.models import Build
from drivers.models import Driver

User = get_user_model()

class RaceFormTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(email="tester@test.com", password="pass")
        self.location = Location.objects.create(display_name="Test Location", owner=self.user)
        self.event = Event.objects.create(display_name="Test Event", owner=self.user)
        self.track = Track.objects.create(display_name="Test Track", owner=self.user)

    def test_race_form_valid(self):
        form_data = {
            'display_name': 'My Race',
            'race_type': 'Lap Race',
            'event': self.event.pk,
            'location': self.location.pk,
            'track': self.track.pk,
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
        self.user = User.objects.create_user(email="driveruser@test.com", password="pass")
        self.race_owner = User.objects.create_user(email="raceowner@test.com", password="pass")
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

class RegisteredRacesResultsTests(TestCase):
    """races:list 'Registered Races' shows my entries' run results."""
    def setUp(self):
        from races.models import RaceDriver
        from stopwatch.models import StopwatchRun
        self.me = User.objects.create_user(email="me@test.com", password="pass")
        self.other = User.objects.create_user(email="other@test.com", password="pass")
        race = Race.objects.create(display_name="Sprint", owner=self.other,
                                   race_type="Stopwatch Race", race_finished=True)
        my_driver = Driver.objects.create(display_name="My Driver", owner=self.me)
        their_driver = Driver.objects.create(display_name="Their Driver", owner=self.other)
        # Registered by someone else, but for a Driver I own -> still mine.
        mine = RaceDriver.objects.create(race=race, user=self.other, driver=my_driver)
        theirs = RaceDriver.objects.create(race=race, user=self.other, driver=their_driver)
        StopwatchRun.objects.create(race=race, racedriver=mine, elapsed_time=12.5)
        StopwatchRun.objects.create(race=race, racedriver=mine, elapsed_time=11.25)
        StopwatchRun.objects.create(race=race, racedriver=theirs, elapsed_time=10.0)

    def test_my_results_listed(self):
        self.client.force_login(self.me)
        resp = self.client.get("/races/")
        races = resp.context['driver_races']
        self.assertEqual(len(races), 1)  # finished races included
        res = races[0].my_results
        self.assertEqual(len(res), 1)    # only my entry, not theirs
        self.assertEqual(res[0]['position'], 2)
        self.assertEqual(len(res[0]['runs']), 2)
        self.assertContains(resp, "Place: #2")
        self.assertNotContains(resp, "Their Driver")
