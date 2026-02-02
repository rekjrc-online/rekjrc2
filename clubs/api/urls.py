from django.urls import path
from posts.api.views import RelatedPostsAPIView
from .views import ClubListAPIView, ClubDetailAPIView
from clubs.models import Club

urlpatterns = [
    path("", ClubListAPIView.as_view(), name="list"),
    path("<uuid:uuid>/", ClubDetailAPIView.as_view(), name="detail"),
    path("<uuid:uuid>/posts/", RelatedPostsAPIView.as_view(model_class=Club), name="posts"),
]
