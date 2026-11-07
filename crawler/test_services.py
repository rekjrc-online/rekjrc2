import json

from django.test import TestCase
from django.urls import reverse

from races.testing_factories import make_entry, make_race, make_user
from . import services
from .models import CrawlerRun


class CrawlerServiceTests(TestCase):
    def setUp(self):
        self.owner = make_user()
        self.race = make_race(self.owner, "Crawler Comp")
        self.a = make_entry(self.race, "A")
        self.b = make_entry(self.race, "B")

    def test_fewest_points_then_fastest(self):
        services.record_run(self.race, self.a, 90.0, 5)
        services.record_run(self.race, self.a, 95.0, 2)     # A's best: 2 pts
        services.record_run(self.race, self.b, 80.0, 2)     # B: 2 pts but faster
        rows = services.sections(self.race)[0].rows
        self.assertEqual([(r.position, r.racedriver) for r in rows], [(1, self.b), (2, self.a)])
        self.assertEqual(rows[1].best.penalty_points, 2)

    def test_untimed_placeholder_does_not_rank_as_zero_points(self):
        CrawlerRun.objects.create(race=self.race, racedriver=self.a)   # old empty row, 0 pts
        services.record_run(self.race, self.b, 80.0, 7)
        rows = services.sections(self.race)[0].rows
        self.assertEqual([(r.position, r.racedriver) for r in rows], [(1, self.b), (None, self.a)])

    def test_view_rerun_keeps_each_runs_log(self):
        self.client.force_login(self.owner)
        url = reverse("crawler:crawl", kwargs={"race_uuid": self.race.uuid, "racedriver_uuid": self.a.uuid})
        log = json.dumps([{"milliseconds": 1000, "label": "[00:01] Gate", "delta": 1}])
        self.client.post(url, {"elapsed_time": "60", "penalty_points": "1", "run_log": log})
        self.client.post(url, {"elapsed_time": "55", "penalty_points": "1", "run_log": log})
        runs = CrawlerRun.objects.filter(racedriver=self.a)
        self.assertEqual(runs.count(), 2)
        self.assertTrue(all(r.log_entries.count() == 1 for r in runs))
