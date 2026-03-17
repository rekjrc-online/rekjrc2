from django.test import TestCase
from django.contrib.auth import get_user_model
from races.models import Race, RaceDriver
from topspeed.models import TopSpeedRun
from topspeed.forms import TopSpeedRunForm
from drivers.models import Driver
from builds.models import Build

User = get_user_model()

class TopSpeedRunTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(email="driver@test.com", password="pass")
        self.race = Race.objects.create(display_name="TopSpeed Test Race", owner=self.user)
        self.driver = Driver.objects.create(display_name="Speedy Driver", owner=self.user)
        self.build = Build.objects.create(display_name="RC Car 1", owner=self.user)
        self.racedriver = RaceDriver.objects.create(
            race=self.race,
            user=self.user,
            driver=self.driver,
            build=self.build)

    def test_topspeedrun_str_with_value(self):
        run = TopSpeedRun.objects.create(
            race=self.race,
            racedriver=self.racedriver,
            topspeed=42.00
        )
        self.assertEqual(str(run), f"{self.racedriver} - 42.00mph")

    def test_topspeedrun_str_without_value(self):
        run = TopSpeedRun.objects.create(
            race=self.race,
            racedriver=self.racedriver)
        self.assertEqual(str(run), f"{self.racedriver} - No top speed recorded")

    def test_topspeedrun_form_valid(self):
        form_data = {'race': self.race.pk, 'racedriver': self.racedriver.pk, 'topspeed': 55.25}
        form = TopSpeedRunForm(data=form_data)
        self.assertTrue(form.is_valid())
        run = form.save()
        self.assertAlmostEqual(float(run.topspeed), 55.25, places=2)
        self.assertEqual(run.race, self.race)
        self.assertEqual(run.racedriver, self.racedriver)

    def test_topspeedrun_form_blank_topspeed(self):
        form_data = {'race': self.race.pk, 'racedriver': self.racedriver.pk, 'topspeed': ''}
        form = TopSpeedRunForm(data=form_data)
        self.assertTrue(form.is_valid())
        run = form.save()
        self.assertIsNone(run.topspeed)
