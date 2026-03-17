from django.test import TestCase
from django.contrib.auth import get_user_model
User = get_user_model()
from races.models import Race, RaceDriver
from drivers.models import Driver
from builds.models import Build
from teams.models import Team, TeamMember
from .models import JudgedScore
from .forms import JudgedScoreForm

class JudgedEventTests(TestCase):

    def setUp(self):
        self.user1 = User.objects.create_user(email='user1@test.com', password='pass')
        self.user2 = User.objects.create_user(email='user2@test.com', password='pass')
        self.judge_team = Team.objects.create(display_name="Judges", owner=self.user1)
        TeamMember.objects.create(team=self.judge_team, user=self.user2)
        self.race = Race.objects.create(
            owner=self.user1,
            display_name='Test Race',
            judge_team=self.judge_team)
        self.driver = Driver.objects.create(display_name="Driver1", owner=self.user1)
        self.build = Build.objects.create(display_name="Build1", owner=self.user1)
        self.racedriver = RaceDriver.objects.create(
            race=self.race,
            user=self.user1,
            driver=self.driver,
            build=self.build)

    def test_judged_score_str(self):
        score = JudgedScore.objects.create(
            race=self.race,
            racedriver=self.racedriver,
            judge=self.user2,
            score=8.5)
        self.assertIn("8.5", str(score))

    def test_judged_score_form_valid(self):
        form_data = {'judge': self.user2.pk, 'score': 9.0}
        form = JudgedScoreForm(data=form_data)
        self.assertTrue(form.is_valid())
        score = form.save(commit=False)
        score.race = self.race
        score.racedriver = self.racedriver
        score.save()
        self.assertEqual(score.score, 9.0)

    def test_judged_score_unique_constraint(self):
        JudgedScore.objects.create(
            race=self.race,
            racedriver=self.racedriver,
            judge=self.user2,
            score=7.0)
        with self.assertRaises(Exception):
            JudgedScore.objects.create(
                race=self.race,
                racedriver=self.racedriver,
                judge=self.user2,
                score=8.0)

    def test_judge_team_members_are_judges(self):
        from judged.views import _is_judge, _judge_count
        self.assertTrue(_is_judge(self.race, self.user2))
        self.assertFalse(_is_judge(self.race, self.user1))
        self.assertEqual(_judge_count(self.race), 1)