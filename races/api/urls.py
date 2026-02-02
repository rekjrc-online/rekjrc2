from django.urls import path
from posts.api.views import RelatedPostsAPIView
from .views import RaceListAPIView, RaceDetailAPIView
from races.models import Race

urlpatterns = [
    path("", RaceListAPIView.as_view(), name="list"),
    path("<uuid:uuid>/", RaceDetailAPIView.as_view(), name="detail"),
    path("<uuid:uuid>/posts/", RelatedPostsAPIView.as_view(model_class=Race), name="posts"),
]
