from django.urls import path
from .views import (
    DeviceListAPIView,
    DeviceDetailAPIView,
    DevicePayloadIngestView,
    DevicePayloadListView,
)

urlpatterns = [
    path("", DeviceListAPIView.as_view(), name="list"),
    path("<int:pk>/", DeviceDetailAPIView.as_view(), name="detail"),
    path("ingest/", DevicePayloadIngestView.as_view(), name="payload-ingest"),
    path("payloads/", DevicePayloadListView.as_view(), name="payload-list"),
]
