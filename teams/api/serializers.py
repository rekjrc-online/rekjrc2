from rest_framework import serializers
from teams.models import Team

class TeamSerializer(serializers.ModelSerializer):
    class Meta:
        model = Team
        fields = [
            "uuid",
            "display_name",
            "avatar",
            "is_active",
        ]
