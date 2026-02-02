from django.test import TestCase
from django.core.exceptions import ValidationError
from races.models import Race, RaceDriver
from .models import LongJumpRun
from .forms import LongJumpRunForm
from django.contrib.auth import get_user_model

User = get_user_model()

class LongJumpRunModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="tester", password="pass")
        self.race = Race.objects.create(display_name="Test Race", owner=self.user, is_active=True)
        self.driver = RaceDriver.objects.create(
            race=self.race,
            user=self.user,
            driver_name="Driver 1",
            model_name="Car 1",
        )

    def test_valid_longjump_run(self):
        run = LongJumpRun.objects.create(
            race=self.race,
            racedriver=self.driver,
            feet=10,
            inches=5
        )
        self.assertEqual(run.total_inches, 10*12 + 5)
        self.assertEqual(str(run), f"{self.driver} - 10ft 5in")

    def test_none_values(self):
        run = LongJumpRun.objects.create(race=self.race, racedriver=self.driver)
        self.assertEqual(run.total_inches, 0)
        self.assertEqual(str(run), f"{self.driver} - No distance recorded")

    def test_feet_out_of_range_raises(self):
        run = LongJumpRun(race=self.race, racedriver=self.driver, feet=1000, inches=5)
        with self.assertRaises(ValidationError):
            run.full_clean()

    def test_inches_out_of_range_raises(self):
        run = LongJumpRun(race=self.race, racedriver=self.driver, feet=5, inches=12)
        with self.assertRaises(ValidationError):
            run.full_clean()

class LongJumpRunFormTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="tester", password="pass")
        self.race = Race.objects.create(display_name="Test Race", owner=self.user, is_active=True)
        self.driver = RaceDriver.objects.create(
            race=self.race,
            user=self.user,
            driver_name="Driver 1",
            model_name="Car 1",
        )

    def test_form_valid_data(self):
        form_data = {
            "race": self.race.pk,
            "racedriver": self.driver.pk,
            "feet": 8,
            "inches": 9
        }
        form = LongJumpRunForm(data=form_data)
        self.assertTrue(form.is_valid())
        run = form.save()
        self.assertEqual(run.total_inches, 8*12 + 9)

    def test_form_invalid_feet(self):
        form_data = {
            "race": self.race.pk,
            "racedriver": self.driver.pk,
            "feet": -1,
            "inches": 5
        }
        form = LongJumpRunForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn("feet", form.errors)

    def test_form_invalid_inches(self):
        form_data = {
            "race": self.race.pk,
            "racedriver": self.driver.pk,
            "feet": 5,
            "inches": 12
        }
        form = LongJumpRunForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn("inches", form.errors)
