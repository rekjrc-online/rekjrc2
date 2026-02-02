from django import forms
from .models import JudgedEventRun, JudgedEventRunScore, Judge

class JudgedEventRunForm(forms.ModelForm):
    class Meta:
        model = JudgedEventRun
        fields = ['race', 'racedriver']

class JudgedEventRunScoreForm(forms.ModelForm):
    class Meta:
        model = JudgedEventRunScore
        fields = ['run', 'judge', 'score']
        widgets = {
            'score': forms.NumberInput(attrs={'step': 0.1, 'min': 0}),
        }

class JudgeForm(forms.ModelForm):
    class Meta:
        model = Judge
        fields = ['race', 'user']
