from rest_framework.generics import ListAPIView, RetrieveAPIView
from locations.models import Location
from .serializers import LocationSerializer

class LocationListAPIView(ListAPIView):
    queryset = Location.objects.filter(is_active=True).order_by("display_name")
    serializer_class = LocationSerializer

class LocationDetailAPIView(RetrieveAPIView):
    queryset = Location.objects.filter(is_active=True)
    serializer_class = LocationSerializer
    lookup_field = "uuid"
