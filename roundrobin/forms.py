from django import forms
from .models import RoundRobinRace


class RoundRobinRaceForm(forms.ModelForm):
    class Meta:
        model  = RoundRobinRace
        fields = ['race', 'model1', 'model2', 'winner']
        widgets = {
            'race':   forms.HiddenInput(),
            'model1': forms.HiddenInput(),
            'model2': forms.HiddenInput(),
            'winner': forms.HiddenInput(),
        }

    def clean(self):
        cleaned_data = super().clean()
        model1 = cleaned_data.get('model1')
        model2 = cleaned_data.get('model2')
        winner = cleaned_data.get('winner')

        if model1 and model2 and model1 == model2:
            self.add_error('model2', 'Lane 2 cannot be the same driver as Lane 1.')

        if winner and winner not in (model1, model2):
            self.add_error('winner', 'Winner must be one of the two competing drivers.')

        return cleaned_data
