from rest_framework import serializers
from clubs.models import Club

class ClubSerializer(serializers.ModelSerializer):
    class Meta:
        model = Club
        fields = [
            "uuid",
            "display_name",
            "avatar",
            "is_active",
        ]
