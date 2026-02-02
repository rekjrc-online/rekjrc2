from rest_framework.generics import ListAPIView, RetrieveAPIView
from races.models import Race
from .serializers import RaceSerializer

class RaceListAPIView(ListAPIView):
    queryset = Race.objects.filter(is_active=True).order_by("display_name")
    serializer_class = RaceSerializer

class RaceDetailAPIView(RetrieveAPIView):
    queryset = Race.objects.filter(is_active=True)
    serializer_class = RaceSerializer
    lookup_field = "uuid"
