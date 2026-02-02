from rest_framework.generics import ListAPIView, RetrieveAPIView
from teams.models import Team
from .serializers import TeamSerializer

class TeamListAPIView(ListAPIView):
    queryset = Team.objects.filter(is_active=True).order_by("display_name")
    serializer_class = TeamSerializer

class TeamDetailAPIView(RetrieveAPIView):
    queryset = Team.objects.filter(is_active=True)
    serializer_class = TeamSerializer
    lookup_field = "uuid"
