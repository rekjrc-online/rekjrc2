from django.urls import path
from posts.api.views import RelatedPostsAPIView
from .views import StoreListAPIView, StoreDetailAPIView
from stores.models import Store

urlpatterns = [
    path("", StoreListAPIView.as_view(), name="list"),
    path("<uuid:uuid>/", StoreDetailAPIView.as_view(), name="detail"),
    path("<uuid:uuid>/posts/", RelatedPostsAPIView.as_view(model_class=Store), name="posts"),
]
