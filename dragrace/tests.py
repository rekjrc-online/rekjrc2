from django.test import TestCase
from django.contrib.auth import get_user_model
User = get_user_model()
from builds.models import Build
from drivers.models import Driver
from races.models import Race, RaceDriver
from .models import DragRace
from .forms import DragRaceForm

class DragRaceTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="user1@test.com",
            password="pass")
        self.race = Race.objects.create(
            display_name="Test Race",
            owner=self.user)
        self.driver1 = Driver.objects.create(
            display_name="Test Driver 1",
            owner=self.user)
        self.build1 = Build.objects.create(
            display_name="Test Build 1",
            owner=self.user)
        self.racedriver1 = RaceDriver.objects.create(
            race=self.race,
            user=self.user,
            driver=self.driver1,
            build=self.build1)
        self.driver2 = Driver.objects.create(
            display_name="Test Driver 2",
            owner=self.user)
        self.build2 = Build.objects.create(
            display_name="Test Build 2",
            owner=self.user)
        self.racedriver2 = RaceDriver.objects.create(
            race=self.race,
            user=self.user,
            driver=self.driver2,
            build=self.build2)

    def test_drag_race_form_valid(self):
        form = DragRaceForm(data={
            "race": self.race.id,
            "model1": self.racedriver1.id,
            "model2": self.racedriver2.id,
            "winner": self.racedriver1.id,
        })
        self.assertTrue(form.is_valid())
        drag_race = form.save()
        self.assertEqual(drag_race.round_number, 1)
        self.assertEqual(drag_race.race, self.race)
        self.assertEqual(drag_race.model1, self.racedriver1)
        self.assertEqual(drag_race.model2, self.racedriver2)
        self.assertEqual(drag_race.winner, self.racedriver1)

    def test_drag_race_form_same_driver_error(self):
        form = DragRaceForm(data={
            "race": self.race.id,
            "model1": self.racedriver1.id,
            "model2": self.racedriver1.id,
        })
        self.assertFalse(form.is_valid())
        self.assertIn("model2", form.errors)
        self.assertEqual(
            form.errors["model2"][0],
            "Lane 2 cannot have the same driver as Lane 1."
        )

    def test_drag_race_str(self):
        drag_race = DragRace.objects.create(
            race=self.race,
            model1=self.racedriver1,
            model2=self.racedriver2,
            winner=self.racedriver1,
            round_number=1,
        )
        output = str(drag_race)
        self.assertIn("Round 1", output)
        self.assertIn(str(self.racedriver1), output)
        self.assertIn(str(self.racedriver2), output)
