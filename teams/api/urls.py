from django.urls import path
from posts.api.views import RelatedPostsAPIView
from .views import TeamListAPIView, TeamDetailAPIView
from teams.models import Team

urlpatterns = [
    path("", TeamListAPIView.as_view(), name="list"),
    path("<uuid:uuid>/", TeamDetailAPIView.as_view(), name="detail"),
    path("<uuid:uuid>/posts/", RelatedPostsAPIView.as_view(model_class=Team), name="posts"),
]
