from django import forms
from .models import Track

class TrackForm(forms.ModelForm):
    class Meta:
        model = Track
        fields = [
            'display_name',
            'owner',
            'is_active',
            'location',
        ]
