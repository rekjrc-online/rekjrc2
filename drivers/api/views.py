from rest_framework.generics import ListAPIView, RetrieveAPIView
from drivers.models import Driver
from .serializers import DriverSerializer

class DriverListAPIView(ListAPIView):
    queryset = Driver.objects.filter(is_active=True).order_by("display_name")
    serializer_class = DriverSerializer

class DriverDetailAPIView(RetrieveAPIView):
    queryset = Driver.objects.filter(is_active=True)
    serializer_class = DriverSerializer
    lookup_field = "uuid"
