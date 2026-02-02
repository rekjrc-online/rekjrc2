from builds.models import Build
from rest_framework.generics import ListAPIView, RetrieveAPIView
from .serializers import BuildSerializer

class BuildListAPIView(ListAPIView):
    queryset = Build.objects.filter(is_active=True).order_by("display_name")
    serializer_class = BuildSerializer

class BuildDetailAPIView(RetrieveAPIView):
    queryset = Build.objects.filter(is_active=True)
    serializer_class = BuildSerializer
    lookup_field = "uuid"
