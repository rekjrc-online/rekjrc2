from django.test import TestCase
from django.contrib.auth import get_user_model
User = get_user_model()
from posts.forms import PostForm
from drivers.models import Driver

class PostFormTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(email="user1@test.com", password="pass")

    def test_post_form_valid_with_driver_author(self):
        driver = Driver.objects.create(display_name="Active", owner=self.user, is_active=True)
        form = PostForm(
            data={
                "content": "Hello world",
                "author_choice": f"driver:{driver.uuid}",},
            author_queryset={
                "driver": Driver.objects.all()},)
        self.assertTrue(form.is_valid())
        post = form.save()
        self.assertEqual(post.author, driver)
        self.assertEqual(post.content, "Hello world")

    def test_post_form_invalid_without_content(self):
        driver = Driver.objects.create(display_name="Active", owner=self.user, is_active=True)
        form = PostForm(
            data = {"content": "", "author_choice": f"driver:{driver.uuid}"},
            author_queryset = {"driver": Driver.objects.all()})
        self.assertFalse(form.is_valid())
        self.assertIn("content", form.errors)

    def test_post_form_uuid_dropdown(self):
        driver = Driver.objects.create(display_name="Active", owner=self.user, is_active=True)
        form = PostForm(
            data = {"content": "Hello", "author_choice": f"driver:{driver.uuid}"},
            author_queryset = {"driver": Driver.objects.all()})
        self.assertTrue(form.is_valid())
        post = form.save()
        self.assertEqual(post.author, driver)

    def test_post_form_rejects_inactive_author(self):
        driver = Driver.objects.create(display_name="Inactive", owner=self.user, is_active=False)
        form = PostForm(
            data = {"content": "Hello", "author_choice": f"driver:{driver.uuid}"},
            author_queryset={"driver": Driver.objects.all()})
        self.assertFalse(form.is_valid())
        self.assertIn("author_choice", form.errors)
