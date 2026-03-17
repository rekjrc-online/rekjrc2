from django.test import TestCase
from django.contrib.auth import get_user_model
User = get_user_model()
from drivers.models import Driver
from posts.models import Post, strip_html, make_clickable_urls
from django.contrib.contenttypes.models import ContentType

class PostModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(email="user1@test.com", password="pass")
        self.driver = Driver.objects.create(display_name="Test Driver", owner=self.user, is_active=True)

    def create_post(self, content="Test post", author=None):
        author = author or self.driver
        post = Post.objects.create(
            content=content,
            author_content_type=ContentType.objects.get_for_model(author),
            author_object_id=author.pk
        )
        return post

    def test_strip_html_function(self):
        text = "<b>Hello</b> <script>alert('x')</script>"
        cleaned = strip_html(text)
        self.assertEqual(cleaned, "Hello alert('x')")

    def test_make_clickable_urls(self):
        text = "Check this out https://example.com"
        result = make_clickable_urls(text)
        self.assertIn('<a href="https://example.com"', result)
        self.assertIn('target="_blank"', result)

    def test_post_save_strips_html_and_sets_display_content(self):
        post = self.create_post(
            content="<b>Hello</b> https://example.com"
        )
        self.assertEqual(post.content, "Hello https://example.com")
        self.assertIn('<a href="https://example.com"', post.display_content)

    def test_posted_date_delta_just_now(self):
        post = self.create_post(content="Test post")
        self.assertEqual(post.posted_date_delta, "just now")

    def test_post_str(self):
        post = self.create_post(content="This is a test post")
        self.assertIn("This is a test post", str(post))
