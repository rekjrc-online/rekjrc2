from django.urls import reverse
from django.contrib.auth import get_user_model
User = get_user_model()
from django.test import TestCase, Client
from drivers.models import Driver
from posts.models import Post, PostLike
from django.contrib.contenttypes.models import ContentType


class ToggleLikeAjaxTests(TestCase):
    """Tests for the toggle_like_ajax view (the heart button endpoint)."""

    def setUp(self):
        self.user = User.objects.create_user(email="liker@test.com", password="pass")
        self.other_user = User.objects.create_user(email="other@test.com", password="pass")
        self.driver = Driver.objects.create(
            display_name="Test Driver", owner=self.user, is_active=True
        )
        self.post = Post.objects.create(
            content="Likeable post",
            author_content_type=ContentType.objects.get_for_model(self.driver),
            author_object_id=self.driver.pk,
        )
        self.url = reverse("posts:ajax_like", kwargs={"post_uuid": self.post.uuid})
        self.client = Client()

    def _login(self, user=None):
        user = user or self.user
        self.client.force_login(user)

    # ── happy path ─────────────────────────────────────────────────────────────

    def test_like_creates_postlike_and_returns_liked_true(self):
        self._login()
        resp = self.client.post(self.url, HTTP_X_CSRFTOKEN="dummy",
                                content_type="application/json")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data["success"])
        self.assertTrue(data["liked"])
        self.assertEqual(data["likes_count"], 1)
        self.assertEqual(PostLike.objects.filter(post=self.post, user=self.user).count(), 1)

    def test_unlike_removes_postlike_and_returns_liked_false(self):
        """Second POST on the same post should toggle the like off."""
        self._login()
        PostLike.objects.create(post=self.post, user=self.user)
        resp = self.client.post(self.url, HTTP_X_CSRFTOKEN="dummy",
                                content_type="application/json")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data["success"])
        self.assertFalse(data["liked"])
        self.assertEqual(data["likes_count"], 0)
        self.assertEqual(PostLike.objects.filter(post=self.post, user=self.user).count(), 0)

    def test_likes_count_reflects_multiple_users(self):
        """likes_count should count all users, not just the requester."""
        self._login()
        PostLike.objects.create(post=self.post, user=self.other_user)
        resp = self.client.post(self.url, HTTP_X_CSRFTOKEN="dummy",
                                content_type="application/json")
        data = resp.json()
        self.assertEqual(data["likes_count"], 2)  # other_user + self.user

    def test_response_includes_post_uuid(self):
        self._login()
        resp = self.client.post(self.url, HTTP_X_CSRFTOKEN="dummy",
                                content_type="application/json")
        data = resp.json()
        self.assertEqual(data["post_uuid"], str(self.post.uuid))

    # ── auth & method guards ───────────────────────────────────────────────────

    def test_unauthenticated_user_is_redirected(self):
        """Anonymous users must not be able to like posts."""
        resp = self.client.post(self.url, content_type="application/json")
        # login_required returns 302 redirect to login page
        self.assertIn(resp.status_code, [302, 403])

    def test_get_request_returns_405(self):
        """Only POST is allowed on this endpoint."""
        self._login()
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 405)

    def test_nonexistent_post_returns_404(self):
        import uuid
        self._login()
        bad_url = reverse("posts:ajax_like", kwargs={"post_uuid": uuid.uuid4()})
        resp = self.client.post(bad_url, HTTP_X_CSRFTOKEN="dummy",
                                content_type="application/json")
        self.assertEqual(resp.status_code, 404)
