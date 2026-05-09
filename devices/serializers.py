from rest_framework import serializers
from devices.models import Device, DevicePayload


class DeviceSerializer(serializers.ModelSerializer):
    owner_type    = serializers.CharField(read_only=True)
    owner_display = serializers.CharField(read_only=True)
    owner_id      = serializers.IntegerField(source='object_id', read_only=True)
    is_unlinked   = serializers.BooleanField(read_only=True)
    claimed_by    = serializers.SerializerMethodField()

    class Meta:
        model  = Device
        fields = [
            "id", "mac", "name", "description",
            "owner_type", "owner_display", "owner_id",
            "is_unlinked", "claimed_by",
            "created_at", "updated_at",
        ]

    def get_claimed_by(self, obj):
        u = obj.claimed_by
        if u is None:
            return None
        return {
            "id": u.id,
            "username": getattr(u, 'username', ''),
            "display": (u.get_full_name() or getattr(u, 'email', '') or str(u)),
        }


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
