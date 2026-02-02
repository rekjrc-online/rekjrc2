from django import forms
from .models import StopwatchRun

class StopwatchRunForm(forms.ModelForm):
    class Meta:
        model = StopwatchRun
        fields = ['race', 'racedriver', 'elapsed_time']
        widgets = {
            'elapsed_time': forms.NumberInput(attrs={'step': '0.01'}),
        }
