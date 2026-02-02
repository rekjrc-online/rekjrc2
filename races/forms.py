from django import forms
from .models import Race, RaceDriver

class RaceForm(forms.ModelForm):
    class Meta:
        model = Race
        fields = [
            'display_name', 'race_type', 'event', 'location', 'track', 
            'club', 'team', 'store', 'transponder', 'entry_locked', 
            'race_finished', 'is_active'
        ]
        widgets = {
            'entry_locked': forms.CheckboxInput(),
            'race_finished': forms.CheckboxInput(),
            'is_active': forms.CheckboxInput(),
        }

class RaceDriverForm(forms.ModelForm):
    class Meta:
        model = RaceDriver
        fields = ['race', 'user', 'build', 'driver', 'transponder']
