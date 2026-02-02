from rest_framework import serializers
from drivers.models import Driver

class DriverSerializer(serializers.ModelSerializer):
    class Meta:
        model = Driver
        fields = [
            "uuid",
            "display_name",
            "avatar",
            "is_active",
        ]
