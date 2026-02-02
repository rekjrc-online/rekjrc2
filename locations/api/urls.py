from django.urls import path
from posts.api.views import RelatedPostsAPIView
from .views import LocationListAPIView, LocationDetailAPIView
from locations.models import Location

urlpatterns = [
    path("", LocationListAPIView.as_view(), name="list"),
    path("<uuid:uuid>/", LocationDetailAPIView.as_view(), name="detail"),
    path("<uuid:uuid>/posts/", RelatedPostsAPIView.as_view(model_class=Location), name="posts"),
]
