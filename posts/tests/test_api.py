from django.urls import reverse
from django.contrib.auth import get_user_model
User = get_user_model()
from django.test import TestCase, Client
from rest_framework.test import APIClient
from rest_framework import status
from drivers.models import Driver
from posts.models import Post, PostLike
from django.contrib.contenttypes.models import ContentType

class PostApiTests(TestCase):
    def setUp(self):
        # Users
        self.user = User.objects.create_user(email="user1@test.com", password="pass")
        self.user2 = User.objects.create_user(email="user2@test.com", password="pass")

        # API client
        self.client = APIClient()

        # Drivers (authors)
        self.driver = Driver.objects.create(display_name="Driver Active", owner=self.user, is_active=True)
        self.inactive_driver = Driver.objects.create(display_name="Driver Inactive", owner=self.user, is_active=False)

        # Helper to create posts
        self.post1 = Post.objects.create(
            content="First post",
            author_content_type=ContentType.objects.get_for_model(self.driver),
            author_object_id=self.driver.pk,
        )
        self.post2 = Post.objects.create(
            content="Second post",
            author_content_type=ContentType.objects.get_for_model(self.driver),
            author_object_id=self.driver.pk,
        )

    def authenticate(self, user=None):
        user = user or self.user
        self.client.force_authenticate(user=user)

    # ---- List and detail endpoints ----
    def test_list_posts(self):
        self.authenticate()
        url = "/api/posts/"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        contents = [item["content"] for item in response.data]
        self.assertIn("First post", contents)
        self.assertIn("Second post", contents)

    def test_post_detail_by_uuid(self):
        self.authenticate()
        url = reverse("posts_api:detail", args=[self.post1.uuid])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["content"], "First post")
        self.assertEqual(response.data["author_info"]["uuid"], str(self.driver.uuid))
        self.assertEqual(response.data["author_info"]["display_name"], self.driver.display_name)
        self.assertEqual(response.data["author_info"]["type"], "Driver")

    def test_driver_related_posts(self):
        from posts.api.views import RelatedPostsAPIView
        view = RelatedPostsAPIView()
        view.model_class = Driver
        view.kwargs = {"uuid": str(self.driver.uuid)}
        qs = view.get_queryset()
        self.assertEqual(len(qs), 2)
        self.assertIn(self.post1, qs)
        self.assertIn(self.post2, qs)

    def test_public_can_list_posts(self):
        self.client.force_authenticate(user=None)
        url = reverse("posts_api:list")
        response = self.client.get(url, format="json")
        self.assertEqual(response.status_code, 403)

    def test_inactive_driver_not_in_related_posts(self):
        post = Post.objects.create(
            content="Inactive driver post",
            author_content_type=ContentType.objects.get_for_model(self.inactive_driver),
            author_object_id=self.inactive_driver.pk)
        from posts.api.views import RelatedPostsAPIView
        view = RelatedPostsAPIView()
        view.model_class = Driver
        view.kwargs = {"uuid": str(self.inactive_driver.uuid)}
        qs = view.get_queryset()
        self.assertIn(post, qs)


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
