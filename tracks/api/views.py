from rest_framework.generics import ListAPIView, RetrieveAPIView
from tracks.models import Track
from .serializers import TrackSerializer

class TrackListAPIView(ListAPIView):
    queryset = Track.objects.filter(is_active=True).order_by("display_name")
    serializer_class = TrackSerializer

class TrackDetailAPIView(RetrieveAPIView):
    queryset = Track.objects.filter(is_active=True)
    serializer_class = TrackSerializer
    lookup_field = "uuid"
