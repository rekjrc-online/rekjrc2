from django.test import TestCase
from django.contrib.auth.models import User
from .models import Build, ATTRIBUTE_NAMES
from .forms import BuildForm

class BuildModelFormTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="tester", password="testpass")

    def test_build_creation(self):
        build = Build.objects.create(
            display_name="Test Build",
            owner=self.user,
            year=2025,
            make="Toyota",
            model="Matrix"
        )
        self.assertEqual(str(build), "Test Build")
        self.assertTrue(build.is_active)
        for attr in ATTRIBUTE_NAMES:
            self.assertEqual(getattr(build, attr) or "", "")
    def test_build_form_valid(self):
        data = {
            'display_name': "Form Build",
            'year': 2025,
            'make': "Honda",
            'model': "Civic",
            'is_active': True }
        for attr in ATTRIBUTE_NAMES:
            data[attr] = ""
        form = BuildForm(data=data, owner=self.user)
        self.assertTrue(form.is_valid())
        build = form.save()
        self.assertEqual(build.owner, self.user)
        self.assertEqual(build.display_name, "Form Build")
        self.assertTrue(build.is_active)

    def test_build_form_invalid_missing_display_name(self):
        data = {'year': 2025, 'make': "Honda", 'model': "Civic", 'is_active': True}
        for attr in ATTRIBUTE_NAMES:
            data[attr] = ""
        form = BuildForm(data=data, owner=self.user)
        self.assertFalse(form.is_valid())
        self.assertIn('display_name', form.errors)

    def test_build_toggle_is_active(self):
        build = Build.objects.create(display_name="Toggle Build", owner=self.user)
        self.assertTrue(build.is_active)
        build.is_active = False
        build.save()
        build.refresh_from_db()
        self.assertFalse(build.is_active)
