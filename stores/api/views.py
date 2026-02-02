from rest_framework.generics import ListAPIView, RetrieveAPIView
from stores.models import Store
from .serializers import StoreSerializer

class StoreListAPIView(ListAPIView):
    queryset = Store.objects.filter(is_active=True).order_by("display_name")
    serializer_class = StoreSerializer

class StoreDetailAPIView(RetrieveAPIView):
    queryset = Store.objects.filter(is_active=True)
    serializer_class = StoreSerializer
    lookup_field = "uuid"
