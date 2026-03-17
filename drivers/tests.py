from django.test import TestCase
from django.contrib.auth import get_user_model
User = get_user_model()
from .models import Driver
from .forms import DriverForm

class DriverModelFormTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(email="user1@test.com", password="pass")

    def test_driver_str(self):
        driver = Driver.objects.create(owner=self.user, display_name="Speedy")
        self.assertEqual(str(driver), "Speedy")
        driver2 = Driver.objects.create(owner=self.user, display_name="")
        self.assertEqual(str(driver2), f"Driver {driver2.pk}")

    def test_driver_form_valid(self):
        form = DriverForm(data={
            'display_name': 'Fast Driver',
            'is_active': True
        })
        self.assertTrue(form.is_valid())
        driver = form.save(commit=False)
        driver.owner = self.user
        driver.save()
        self.assertEqual(driver.display_name, "Fast Driver")
        self.assertTrue(driver.is_active)

    def test_driver_form_empty_display_name(self):
        form = DriverForm(data={
            "display_name": "",
            "is_active": False,
        })
        self.assertFalse(form.is_valid())
        self.assertIn("display_name", form.errors)

