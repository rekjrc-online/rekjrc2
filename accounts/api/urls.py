from django.urls import path
from .views import CurrentUserAPIView

urlpatterns = [
    path("", CurrentUserAPIView.as_view(), name="list"),
]
