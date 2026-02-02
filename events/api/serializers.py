from rest_framework import serializers
from events.models import Event

class EventSerializer(serializers.ModelSerializer):
    class Meta:
        model = Event
        fields = [
            "uuid",
            "display_name",
            "avatar",
            "is_active",
        ]
