from django.urls import path
from posts.api.views import RelatedPostsAPIView
from .views import EventListAPIView, EventDetailAPIView
from events.models import Event

urlpatterns = [
    path("", EventListAPIView.as_view(), name="list"),
    path("<uuid:uuid>/", EventDetailAPIView.as_view(), name="detail"),
    path("<uuid:uuid>/posts/", RelatedPostsAPIView.as_view(model_class=Event), name="posts"),
]
