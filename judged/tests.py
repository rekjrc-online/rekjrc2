from django.test import TestCase
from django.contrib.auth.models import User
from races.models import Race, RaceDriver
from .models import JudgedEventRun, JudgedEventRunScore, Judge
from .forms import JudgedEventRunForm, JudgedEventRunScoreForm, JudgeForm

class JudgedEventTests(TestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(username='user1', password='pass')
        self.user2 = User.objects.create_user(username='user2', password='pass')
        self.race = Race.objects.create(owner=self.user1, display_name='Test Race')
        self.driver = RaceDriver.objects.create(race=self.race, user=self.user1, driver_name='Driver1', model_name='ModelX')

    def test_judged_event_run_str_no_scores(self):
        run = JudgedEventRun.objects.create(race=self.race, racedriver=self.driver)
        self.assertIn("No score recorded", str(run))

    def test_judged_event_run_form_valid(self):
        form_data = {'race': self.race.pk, 'racedriver': self.driver.pk}
        form = JudgedEventRunForm(data=form_data)
        self.assertTrue(form.is_valid())
        run = form.save()
        self.assertEqual(run.racedriver, self.driver)

    def test_judged_event_run_score_str_and_form(self):
        run = JudgedEventRun.objects.create(race=self.race, racedriver=self.driver)
        score = JudgedEventRunScore.objects.create(run=run, judge=self.user1, score=8.5)
        self.assertIn("8.5", str(score))

        form_data = {'run': run.pk, 'judge': self.user2.pk, 'score': 9.0}
        form = JudgedEventRunScoreForm(data=form_data)
        self.assertTrue(form.is_valid())
        new_score = form.save()
        self.assertEqual(new_score.score, 9.0)

    def test_judge_unique_constraint_and_limit(self):
        Judge.objects.create(race=self.race, user=self.user1)
        Judge.objects.create(race=self.race, user=self.user2)

        # Attempting to create a 3rd judge is allowed
        user3 = User.objects.create_user(username='user3', password='pass')
        judge3 = Judge(race=self.race, user=user3)
        judge3.clean()  # Should not raise yet
        judge3.save()

        # Attempting to add a 4th judge should raise ValidationError
        user4 = User.objects.create_user(username='user4', password='pass')
        judge4 = Judge(race=self.race, user=user4)
        with self.assertRaises(Exception):
            judge4.clean()
