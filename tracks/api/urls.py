from django.urls import path
from posts.api.views import RelatedPostsAPIView
from .views import TrackListAPIView, TrackDetailAPIView
from tracks.models import Track

urlpatterns = [
    path("", TrackListAPIView.as_view(), name="list"),
    path("<uuid:uuid>/", TrackDetailAPIView.as_view(), name="detail"),
    path("<uuid:uuid>/posts/", RelatedPostsAPIView.as_view(model_class=Track), name="posts"),
]
