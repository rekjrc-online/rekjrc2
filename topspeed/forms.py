from django import forms
from .models import TopSpeedRun

class TopSpeedRunForm(forms.ModelForm):
    class Meta:
        model = TopSpeedRun
        fields = [
            'race',
            'racedriver',
            'topspeed',
        ]
