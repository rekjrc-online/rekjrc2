from django.test import TestCase
from django.urls import reverse

from races.testing_factories import make_entry, make_race, make_user
from . import services
from .models import LongJumpRun


class LongJumpServiceTests(TestCase):
    def setUp(self):
        self.owner = make_user()
        self.race = make_race(self.owner, "Long Jump")
        self.a = make_entry(self.race, "A")
        self.b = make_entry(self.race, "B")

    def test_longest_jump_is_best(self):
        services.record_jump(self.race, self.a, 10, 11)
        services.record_jump(self.race, self.a, 11, 0)
        services.record_jump(self.race, self.b, 10, 6)
        rows = services.sections(self.race)[0].rows
        self.assertEqual([(r.position, r.racedriver, r.best_display) for r in rows],
                         [(1, self.a, "11ft 0in"), (2, self.b, "10ft 6in")])

    def test_parse_distance(self):
        self.assertEqual(services.parse_distance("12", "7"), (12, 7))
        for bad in (("", "1"), ("1", "12"), ("-1", "0"), ("1000", "0"), ("0", "0"), (None, None)):
            self.assertIsNone(services.parse_distance(*bad), bad)

    def test_view_rerun(self):
        self.client.force_login(self.owner)
        url = reverse("longjump:race", kwargs={"race_uuid": self.race.uuid, "racedriver_uuid": self.a.uuid})
        self.client.post(url, {"feet": "5", "inches": "2"})
        self.client.post(url, {"feet": "6", "inches": "1"})
        self.assertEqual(LongJumpRun.objects.filter(racedriver=self.a).count(), 2)
