from django.test import TestCase
from django.contrib.auth import get_user_model
from teams.models import Team, TeamMember
from teams.forms import TeamForm, TeamMemberForm

User = get_user_model()

class TeamTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="owner", password="pass")

    def test_team_form_valid(self):
        form_data = {
            'display_name': "Test Team",
            'is_active': True,
            'description': "A test team"
        }
        form = TeamForm(data=form_data)
        self.assertTrue(form.is_valid())
        team = form.save(commit=False)
        team.owner = self.user
        team.save()
        self.assertEqual(team.display_name, "Test Team")
        self.assertTrue(team.is_active)
        self.assertEqual(str(team), "Test Team")

    def test_team_form_blank_optional_fields(self):
        form_data = {
            'display_name': "Minimal Team",
            'is_active': False
        }
        form = TeamForm(data=form_data)
        self.assertTrue(form.is_valid())
        team = form.save(commit=False)
        team.owner = self.user
        team.save()
        self.assertFalse(team.is_active)

    def test_team_member_form_valid(self):
        team = Team.objects.create(display_name="Member Team", owner=self.user)
        form_data = {'team': team.pk, 'user': self.user.pk}
        form = TeamMemberForm(data=form_data)
        self.assertTrue(form.is_valid())
        member = form.save()
        self.assertEqual(member.team, team)
        self.assertEqual(member.user, self.user)
        self.assertEqual(str(member), f"{self.user} @ {team}")

    def test_team_member_unique_constraint(self):
        team = Team.objects.create(display_name="Unique Team", owner=self.user)
        member = TeamMember.objects.create(team=team, user=self.user)
        form_data = {'team': team.pk, 'user': self.user.pk}
        form = TeamMemberForm(data=form_data)
        self.assertFalse(form.is_valid())
        with self.assertRaises(Exception):
            form.save()
