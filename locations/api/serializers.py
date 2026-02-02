from rest_framework import serializers
from locations.models import Location

class LocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Location
        fields = [
            "uuid",
            "display_name",
            "avatar",
            "is_active",
        ]
