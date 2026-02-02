from django.test import TestCase
from races.models import Race, RaceDriver
from .models import CrawlerRun, CrawlerRunLog
from .forms import CrawlerRunForm
from django.contrib.auth.models import User

class CrawlerTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="user1",
            password="pass")
        self.race = Race.objects.create(
            display_name="Test Race",
            owner=self.user)
        self.driver = RaceDriver.objects.create(
            race=self.race,
            user=self.user,
            driver_name="Driver 1",
            model_name="Test Car")

    def test_crawler_run_form_save(self):
        form = CrawlerRunForm(data={
            "race": self.race.id,
            "racedriver": self.driver.id,
            "elapsed_time": 12.34,
            "penalty_points": 5
        })
        self.assertTrue(form.is_valid())
        run = form.save()
        self.assertEqual(run.race, self.race)
        self.assertEqual(run.racedriver, self.driver)
        self.assertEqual(run.elapsed_time, 12.34)
        self.assertEqual(run.penalty_points, 5)

    def test_total_log_points_empty(self):
        run = CrawlerRun.objects.create(race=self.race, racedriver=self.driver)
        self.assertEqual(run.total_log_points(), 0)

    def test_total_log_points_with_entries(self):
        run = CrawlerRun.objects.create(race=self.race, racedriver=self.driver)
        CrawlerRunLog.objects.create(run=run, milliseconds=1000, label="Lap 1", delta=2)
        CrawlerRunLog.objects.create(run=run, milliseconds=2000, label="Lap 2", delta=3)
        self.assertEqual(run.total_log_points(), 5)

    def test_crawler_run_str_representation(self):
        run = CrawlerRun.objects.create(race=self.race, racedriver=self.driver, elapsed_time=15.67, penalty_points=2)
        self.assertIn("Driver 1", str(run))
        self.assertIn("15.67", str(run))
        self.assertIn("2", str(run))

    def test_crawler_runlog_str_representation(self):
        run = CrawlerRun.objects.create(race=self.race, racedriver=self.driver)
        log = CrawlerRunLog.objects.create(run=run, milliseconds=1234, label="Test Lap", delta=1)
        self.assertEqual(str(log), "1234ms - Test Lap (+1)")
