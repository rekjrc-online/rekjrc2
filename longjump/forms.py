from django import forms
from .models import LongJumpRun

class LongJumpRunForm(forms.ModelForm):
    class Meta:
        model = LongJumpRun
        fields = ['race', 'racedriver', 'feet', 'inches']
        widgets = {
            'feet': forms.NumberInput(attrs={'min': 0, 'max': 999}),
            'inches': forms.NumberInput(attrs={'min': 0, 'max': 11}),
        }
