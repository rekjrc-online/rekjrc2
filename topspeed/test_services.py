from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from races.testing_factories import make_entry, make_race, make_user
from . import services
from .models import TopSpeedRun


class TopSpeedServiceTests(TestCase):
    def setUp(self):
        self.owner = make_user()
        self.race = make_race(self.owner, "Top Speed")
        self.a = make_entry(self.race, "A")
        self.b = make_entry(self.race, "B")

    def test_every_submission_is_kept_and_best_wins(self):
        services.record_topspeed(self.race, self.a, "40.10")
        services.record_topspeed(self.race, self.a, "45.20")
        services.record_topspeed(self.race, self.a, "42.00")
        self.assertEqual(TopSpeedRun.objects.filter(racedriver=self.a).count(), 3)
        row = next(r for r in services.sections(self.race)[0].rows if r.racedriver == self.a)
        self.assertEqual(row.attempts, 3)
        self.assertEqual(row.best.topspeed, Decimal("45.20"))
        self.assertEqual(row.best_display, "45.20 mph")

    def test_placeholder_runs_ignored(self):
        TopSpeedRun.objects.create(race=self.race, racedriver=self.a)   # old empty row
        row = next(r for r in services.sections(self.race)[0].rows if r.racedriver == self.a)
        self.assertEqual(row.attempts, 0)
        self.assertIsNone(row.position)
        self.assertFalse(services.finish(self.race))

    def test_ties(self):
        services.record_topspeed(self.race, self.a, "50")
        services.record_topspeed(self.race, self.b, "50")
        self.assertEqual([r.position for r in services.sections(self.race)[0].rows], [1, 1])

    def test_parse_mph(self):
        self.assertEqual(services.parse_mph("45.2"), Decimal("45.20"))
        for bad in (None, "", "abc", "0", "-3", "1000", "nan", "inf"):
            self.assertIsNone(services.parse_mph(bad), bad)


class TopSpeedViewTests(TestCase):
    def setUp(self):
        self.owner = make_user()
        self.race = make_race(self.owner, "Top Speed")
        self.a = make_entry(self.race, "A")
        self.client.force_login(self.owner)
        self.url = reverse("topspeed:race", kwargs={"race_uuid": self.race.uuid, "racedriver_uuid": self.a.uuid})

    def test_get_does_not_create_a_placeholder_run(self):
        self.assertEqual(self.client.get(self.url).status_code, 200)
        self.assertFalse(TopSpeedRun.objects.exists())

    def test_rerun_post_creates_a_second_run(self):
        self.client.post(self.url, {"topspeed": "40"})
        self.client.post(self.url, {"topspeed": "41"})
        self.assertEqual(TopSpeedRun.objects.filter(racedriver=self.a).count(), 2)

    def test_start_page_renders(self):
        self.client.post(self.url, {"topspeed": "40"})
        resp = self.client.get(reverse("topspeed:start", kwargs={"race_uuid": self.race.uuid}))
        self.assertContains(resp, "40.00 mph")
        self.assertContains(resp, "Re-run")
