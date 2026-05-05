from django.utils import timezone
from rest_framework import status
from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework.response import Response
from rest_framework.views import APIView
from devices.models import Device, DevicePayload
from .serializers import DeviceSerializer, DevicePayloadSerializer


class DeviceListAPIView(ListAPIView):
    queryset = Device.objects.all().order_by("name")
    serializer_class = DeviceSerializer


class DeviceDetailAPIView(RetrieveAPIView):
    queryset = Device.objects.all()
    serializer_class = DeviceSerializer
    lookup_field = "uuid"


class DevicePayloadIngestView(APIView):
    """
    POST /api/devices/ingest/
    Accepts a payload from the ESP-NOW gateway (or any source)
    and writes it to DevicePayload.

    Body (JSON):
        node          — MAC address string "AA:BB:CC:DD:EE:FF"
        value         — measurement string e.g. "75.51"
        name          — driver display name (may be empty)
        racedriver_id — Django RaceDriver pk (may be 0 or absent)

    Unknown devices are auto-created with name = MAC.
    """
    def post(self, request):
        mac = request.data.get("node", "").upper().strip()
        value = request.data.get("value", "").strip()
        name = request.data.get("name", "").strip()
        racedriver_id = request.data.get("racedriver_id") or None

        if not mac or not value:
            return Response(
                {"error": "node and value are required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        device, _ = Device.objects.get_or_create(mac=mac, defaults={"name": mac})

        payload = DevicePayload.objects.create(
            device=device,
            value=value[:32],
            name=name[:40],
            racedriver_id=int(racedriver_id) if racedriver_id else None,
        )

        return Response({"id": payload.id}, status=status.HTTP_201_CREATED)


class DevicePayloadListView(ListAPIView):
    """
    GET /api/devices/payloads/?processed=false&device=AA:BB:CC:DD:EE:FF
    """
    serializer_class = DevicePayloadSerializer

    def get_queryset(self):
        qs = DevicePayload.objects.select_related("device").all()
        processed = self.request.query_params.get("processed")
        mac = self.request.query_params.get("device")
        if processed is not None:
            qs = qs.filter(processed=processed.lower() != "false")
        if mac:
            qs = qs.filter(device__mac=mac.upper())
        return qs
