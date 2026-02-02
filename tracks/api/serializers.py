from rest_framework import serializers
from tracks.models import Track

class TrackSerializer(serializers.ModelSerializer):
    class Meta:
        model = Track
        fields = [
            "uuid",
            "display_name",
            "avatar",
            "is_active",
        ]
