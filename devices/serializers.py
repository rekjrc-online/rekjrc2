from rest_framework import serializers
from devices.models import Device, DevicePayload

class DeviceSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Device
        fields = ["id", "mac", "name", "description", "created_at", "updated_at"]

class DevicePayloadSerializer(serializers.ModelSerializer):
    device_mac  = serializers.CharField(source='device.mac', read_only=True)
    device_name = serializers.CharField(source='device.name', read_only=True)

    class Meta:
        model  = DevicePayload
        fields = [
            "id", "device", "device_mac", "device_name",
            "created_at", "racedriver_id", "value", "name",
            "processed", "processed_at", "error", "retry_count",
        ]
        read_only_fields = [
            "created_at", "processed_at", "device_mac", "device_name",
        ]
