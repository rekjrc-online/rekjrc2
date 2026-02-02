from django.urls import path
from posts.api.views import RelatedPostsAPIView
from .views import DriverListAPIView, DriverDetailAPIView
from drivers.models import Driver

urlpatterns = [
    path("", DriverListAPIView.as_view(), name="list"),
    path("<uuid:uuid>/", DriverDetailAPIView.as_view(), name="detail"),
    path("<uuid:uuid>/posts/", RelatedPostsAPIView.as_view(model_class=Driver), name="posts"),
]
