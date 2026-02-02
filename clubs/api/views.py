from rest_framework.generics import ListAPIView, RetrieveAPIView
from clubs.models import Club
from .serializers import ClubSerializer

class ClubListAPIView(ListAPIView):
    queryset = Club.objects.filter(is_active=True).order_by("display_name")
    serializer_class = ClubSerializer

class ClubDetailAPIView(RetrieveAPIView):
    queryset = Club.objects.filter(is_active=True)
    serializer_class = ClubSerializer
    lookup_field = "uuid"
