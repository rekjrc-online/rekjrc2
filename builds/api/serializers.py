from rest_framework import serializers
from builds.models import Build

class BuildSerializer(serializers.ModelSerializer):
    class Meta:
        model = Build
        fields = [
            "uuid",
            "display_name",
            "avatar",
            "is_active",
        ]
