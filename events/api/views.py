from rest_framework.generics import ListAPIView, RetrieveAPIView
from events.models import Event
from .serializers import EventSerializer

class EventListAPIView(ListAPIView):
    queryset = Event.objects.filter(is_active=True).order_by("display_name")
    serializer_class = EventSerializer

class EventDetailAPIView(RetrieveAPIView):
    queryset = Event.objects.filter(is_active=True)
    serializer_class = EventSerializer
    lookup_field = "uuid"
