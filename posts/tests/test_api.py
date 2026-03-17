from django.urls import reverse
from django.contrib.auth import get_user_model
User = get_user_model()
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from drivers.models import Driver
from posts.models import Post
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
