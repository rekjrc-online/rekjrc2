from django.test import TestCase
from django.contrib.auth import get_user_model
from locations.models import Location
from stores.forms import StoreForm

User = get_user_model()

class StoreFormTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(email="owner@test.com", password="pass")
        self.location = Location.objects.create(display_name="Test Location", owner=self.user)

    def test_store_form_valid(self):
        form_data = {
            'display_name': "Test Store",
            'is_active': True,
            'location': self.location.pk,
            'description': "A test store",
            'website': "https://example.com",
            'email': "test@example.com",
            'phone_number': "123-456-7890"
        }
        form = StoreForm(data=form_data)
        self.assertTrue(form.is_valid())
        store = form.save(commit=False)
        store.owner = self.user
        store.save()
        self.assertEqual(store.display_name, "Test Store")
        self.assertTrue(store.is_active)
        self.assertEqual(str(store), "Test Store")

    def test_store_form_blank_optional_fields(self):
        form_data = {
            'display_name': "Minimal Store",
            'is_active': False,
            'location': self.location.pk
        }
        form = StoreForm(data=form_data)
        self.assertTrue(form.is_valid())
        store = form.save(commit=False)
        store.owner = self.user
        store.save()
        self.assertEqual(store.description, "")
        self.assertEqual(store.website, None)
        self.assertFalse(store.is_active)

    def test_store_form_invalid_missing_display_name(self):
        form_data = {'is_active': True, 'location': self.location.pk}
        form = StoreForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('display_name', form.errors)