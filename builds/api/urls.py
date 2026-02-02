from django.urls import path
from posts.api.views import RelatedPostsAPIView
from .views import BuildListAPIView, BuildDetailAPIView
from builds.models import Build

urlpatterns = [
    path("", BuildListAPIView.as_view(), name="list"),
    path("<uuid:uuid>/", BuildDetailAPIView.as_view(), name="detail"),
    path("<uuid:uuid>/posts/", RelatedPostsAPIView.as_view(model_class=Build), name="posts"),
]
