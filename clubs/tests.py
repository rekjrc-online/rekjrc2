from django.test import TestCase
from django.contrib.auth.models import User
from locations.models import Location
from .models import Club, ClubLocation, ClubMember
from .forms import ClubForm
from .forms import ClubLocationForm
from .forms import ClubMemberForm

class ClubTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(username="owner", password="pass")
        self.user = User.objects.create_user(username="member", password="pass")
        self.location = Location.objects.create(display_name="Test Location", owner=self.owner, latitude=0, longitude=0)

    def test_club_form_save_with_owner(self):
        form = ClubForm(data={"display_name": "My Club", "is_active": True}, owner=self.owner)
        self.assertTrue(form.is_valid())
        club = form.save()
        self.assertEqual(club.owner, self.owner)
        self.assertEqual(club.display_name, "My Club")
        self.assertTrue(club.is_active)

    def test_club_location_form_sets_club(self):
        club = Club.objects.create(display_name="Test Club", owner=self.owner)
        form = ClubLocationForm(data={"location": self.location.id}, club=club)
        self.assertTrue(form.is_valid())
        club_location = form.save()
        self.assertEqual(club_location.club, club)
        self.assertEqual(club_location.location, self.location)

    def test_club_member_form_sets_club(self):
        club = Club.objects.create(display_name="Test Club", owner=self.owner)
        form = ClubMemberForm(data={"user": self.user.id, "role": "Driver"}, club=club)
        self.assertTrue(form.is_valid())
        member = form.save()
        self.assertEqual(member.club, club)
        self.assertEqual(member.user, self.user)
        self.assertEqual(member.role, "Driver")

    def test_unique_club_location_constraint(self):
        club = Club.objects.create(display_name="Test Club", owner=self.owner)
        ClubLocation.objects.create(club=club, location=self.location)
        form = ClubLocationForm(data={"location": self.location.id}, club=club)
        self.assertFalse(form.is_valid())
        self.assertIn("__all__", form.errors)

    def test_unique_club_member_constraint(self):
        club = Club.objects.create(display_name="Test Club", owner=self.owner)
        ClubMember.objects.create(club=club, user=self.user, role="Driver")
        form = ClubMemberForm(data={"user": self.user.id, "role": "Driver"}, club=club)
        self.assertFalse(form.is_valid())
        self.assertIn("__all__", form.errors)
