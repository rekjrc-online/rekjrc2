from django.test import TestCase
from django.contrib.auth import get_user_model
from races.models import Race, RaceDriver
from stopwatch.models import StopwatchRun
from stopwatch.forms import StopwatchRunForm

User = get_user_model()

class StopwatchRunFormTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="raceowner", password="pass")
        self.race = Race.objects.create(display_name="Race1", owner=self.user)
        self.driver_user = User.objects.create_user(username="driver", password="pass")
        self.racedriver = RaceDriver.objects.create(
            race=self.race,
            user=self.driver_user,
            model_name="Model X",
            driver_name="John Doe",
        )

    def test_stopwatch_run_form_valid(self):
        form_data = {
            'race': self.race.pk,
            'racedriver': self.racedriver.pk,
            'elapsed_time': 12.34
        }
        form = StopwatchRunForm(data=form_data)
        self.assertTrue(form.is_valid())
        run = form.save()
        self.assertEqual(run.elapsed_time, 12.34)
        self.assertEqual(str(run), f"{self.racedriver} - 12.34s")

    def test_stopwatch_run_form_blank_elapsed_time(self):
        form_data = {
            'race': self.race.pk,
            'racedriver': self.racedriver.pk,
            'elapsed_time': None
        }
        form = StopwatchRunForm(data=form_data)
        self.assertTrue(form.is_valid())
        run = form.save()
        self.assertIsNone(run.elapsed_time)
        self.assertEqual(str(run), f"{self.racedriver} - No time recorded")

    def test_stopwatch_run_form_invalid_missing_required(self):
        form = StopwatchRunForm(data={})
        self.assertFalse(form.is_valid())
        self.assertIn('race', form.errors)
        self.assertIn('racedriver', form.errors)
