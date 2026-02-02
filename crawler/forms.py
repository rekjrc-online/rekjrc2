from django import forms
from .models import CrawlerRun, CrawlerRunLog

class CrawlerRunForm(forms.ModelForm):
    class Meta:
        model = CrawlerRun
        fields = [
            'race',
            'racedriver',
            'elapsed_time',
            'penalty_points',
        ]
        widgets = {
            'race': forms.HiddenInput(),
            'racedriver': forms.HiddenInput(),
        }
