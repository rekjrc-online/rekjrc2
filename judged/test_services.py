from django.test import TestCase
from django.urls import reverse

from races.testing_factories import make_entry, make_race, make_user
from teams.models import Team, TeamMember
from . import services
from .models import JudgedScore


class JudgedRerunTests(TestCase):
    def setUp(self):
        self.owner = make_user()
        self.j1, self.j2 = make_user(), make_user()
        team = Team.objects.create(display_name="Judges", owner=self.owner)
        TeamMember.objects.create(team=team, user=self.j1)
        TeamMember.objects.create(team=team, user=self.j2)
        self.race = make_race(self.owner, "Judged Event", judge_team=team)
        self.a = make_entry(self.race, "A")
        self.b = make_entry(self.race, "B")

    def test_scores_fill_runs_in_order_even_out_of_step(self):
        s1 = services.record_score(self.race, self.a, self.j1, 8)   # j1 -> run 1
        s2 = services.record_score(self.race, self.a, self.j1, 9)   # j1 -> run 2 (j2 hasn't scored run 1)
        s3 = services.record_score(self.race, self.a, self.j2, 7)   # j2 -> run 1 (lowest it lacks)
        s4 = services.record_score(self.race, self.a, self.j2, 6)   # j2 -> run 2
        self.assertEqual([s.run_number for s in (s1, s2, s3, s4)], [1, 2, 1, 2])

    def test_best_complete_run_ranks_and_incomplete_runs_dont(self):
        for judge, score in ((self.j1, 8), (self.j2, 7)):      # A run 1 = 15
            services.record_score(self.race, self.a, judge, score)
        for judge, score in ((self.j1, 9), (self.j2, 9)):      # A run 2 = 18
            services.record_score(self.race, self.a, judge, score)
        services.record_score(self.race, self.a, self.j1, 10)  # A run 3: 1/2 judges
        for judge, score in ((self.j1, 8), (self.j2, 8)):      # B run 1 = 16
            services.record_score(self.race, self.b, judge, score)

        secs = services.sections(self.race)
        rows = secs[0].rows
        self.assertEqual([(r.position, r.racedriver) for r in rows], [(1, self.a), (2, self.b)])
        self.assertEqual(rows[0].best.run_number, 2)
        self.assertEqual(rows[0].best_display, "18.0")
        self.assertEqual([(rd, run.run_number) for rd, run in services.incomplete_runs(secs)],
                         [(self.a, 3)])

    def test_finish_asks_to_confirm_when_runs_incomplete(self):
        services.record_score(self.race, self.a, self.j1, 8)
        services.record_score(self.race, self.a, self.j2, 8)
        services.record_score(self.race, self.b, self.j1, 5)   # B: incomplete
        self.client.force_login(self.owner)
        url = reverse("judged:finish", kwargs={"race_uuid": self.race.uuid})

        resp = self.client.post(url)
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Finish Race Anyway")
        self.race.refresh_from_db()
        self.assertFalse(self.race.race_finished)

        self.client.post(url, {"confirm": "1"})
        self.race.refresh_from_db()
        self.assertTrue(self.race.race_finished)

    def test_judge_view_allows_rescoring(self):
        self.client.force_login(self.j1)
        url = reverse("judged:judge", kwargs={"race_uuid": self.race.uuid, "racedriver_id": self.a.id})
        self.client.post(url, {"score": "7.5"})
        resp = self.client.get(url)
        self.assertContains(resp, "Run 2")
        self.client.post(url, {"score": "8.5"})
        self.assertEqual(
            list(JudgedScore.objects.filter(racedriver=self.a).values_list('run_number', flat=True).order_by('run_number')),
            [1, 2])
        start = self.client.get(reverse("judged:start", kwargs={"race_uuid": self.race.uuid}))
        self.assertContains(start, "Score run 3")
