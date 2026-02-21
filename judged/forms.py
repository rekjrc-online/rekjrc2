from django import forms
from .models import JudgedScore

class JudgedScoreForm(forms.ModelForm):
    class Meta:
        model = JudgedScore
        fields = ['judge', 'score']
        widgets = {
            'score': forms.NumberInput(attrs={'step': 0.1, 'min': 0}),
        }