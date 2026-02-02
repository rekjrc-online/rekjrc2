from django.test import TestCase
from django.contrib.auth.models import User

from races.models import Race, RaceDriver
from .models import DragRace
from .forms import DragRaceForm


class DragRaceTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="user1",
            password="pass"
        )
        self.race = Race.objects.create(
            display_name="Test Race",
            owner=self.user
        )
        self.driver1 = RaceDriver.objects.create(
            race=self.race,
            user=self.user,
            driver_name="Driver 1",
            model_name="Model 1"
)
        self.driver2 = RaceDriver.objects.create(
            race=self.race,
            user=self.user,
            driver_name="Driver 2",
            model_name="Model 2"
        )

    def test_drag_race_form_valid(self):
        form = DragRaceForm(data={
            "race": self.race.id,
            "model1": self.driver1.id,
            "model2": self.driver2.id,
            "winner": self.driver1.id,
        })
        self.assertTrue(form.is_valid())
        drag_race = form.save()
        self.assertEqual(drag_race.round_number, 1)
        self.assertEqual(drag_race.race, self.race)
        self.assertEqual(drag_race.model1, self.driver1)
        self.assertEqual(drag_race.model2, self.driver2)
        self.assertEqual(drag_race.winner, self.driver1)

    def test_drag_race_form_same_driver_error(self):
        form = DragRaceForm(data={
            "race": self.race.id,
            "model1": self.driver1.id,
            "model2": self.driver1.id,
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
            model1=self.driver1,
            model2=self.driver2,
            winner=self.driver1,
            round_number=1,
        )
        output = str(drag_race)
        self.assertIn("Round 1", output)
        self.assertIn(str(self.driver1), output)
        self.assertIn(str(self.driver2), output)
