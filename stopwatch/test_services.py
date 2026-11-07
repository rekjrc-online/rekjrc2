from django.test import TestCase
from django.urls import reverse

from posts.models import Post
from races.testing_factories import make_entry, make_race, make_user
from . import services
from .models import StopwatchRun


class StopwatchServiceTests(TestCase):
    def setUp(self):
        self.owner = make_user()
        self.race = make_race(self.owner, "Rally")
        self.a = make_entry(self.race, "A")
        self.b = make_entry(self.race, "B")

    def test_lowest_time_is_best(self):
        services.record_time(self.race, self.a, 14.0)
        services.record_time(self.race, self.a, 12.5)
        services.record_time(self.race, self.b, 13.0)
        rows = services.sections(self.race)[0].rows
        self.assertEqual([(r.position, r.racedriver, r.best.elapsed_time) for r in rows],
                         [(1, self.a, 12.5), (2, self.b, 13.0)])

    def test_zero_placeholder_ignored(self):
        StopwatchRun.objects.create(race=self.race, racedriver=self.a, elapsed_time=0)
        self.assertEqual(services.sections(self.race)[0].rows[0].attempts, 0)

    def test_finish_with_no_times_still_closes_race(self):
        services.finish(self.race)
        self.race.refresh_from_db()
        self.assertTrue(self.race.race_finished)
        self.assertIn("No stopwatch times recorded",
                      Post.objects.filter(author_object_id=self.race.id).latest('id').content)


class StopwatchViewTests(TestCase):
    def test_rerun_post_creates_a_second_run(self):
        owner = make_user()
        race = make_race(owner, "Stopwatch Race")
        a = make_entry(race, "A")
        self.client.force_login(owner)
        url = reverse("stopwatch:race", kwargs={"race_uuid": race.uuid, "racedriver_uuid": a.uuid})
        self.assertEqual(self.client.get(url + "?mode=enter").status_code, 200)
        self.client.post(url, {"elapsed_time": "12.34"})
        self.client.post(url, {"elapsed_time": "11.00"})
        self.client.post(url, {"elapsed_time": "0"})   # untimed submit: ignored
        self.assertEqual(StopwatchRun.objects.filter(racedriver=a).count(), 2)
