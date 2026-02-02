from django.urls import path
from .views import PostListAPIView, PostDetailAPIView

app_name = 'posts_api'

urlpatterns = [
    path("", PostListAPIView.as_view(), name="list"),
    path("<uuid:uuid>/", PostDetailAPIView.as_view(), name="detail"),
]
