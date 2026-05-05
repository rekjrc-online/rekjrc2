from django import forms
from .models import DragDouble

class DragDoubleForm(forms.ModelForm):
    class Meta:
        model = DragDouble
        fields = [
            'race',
            'model1',
            'model2',
            'winner',
        ]
        widgets = {
            'race': forms.HiddenInput(),
            'model1': forms.HiddenInput(),
            'model2': forms.HiddenInput(),
            'winner': forms.HiddenInput(),
        }

    def clean(self):
        cleaned_data = super().clean()
        model1 = cleaned_data.get('model1')
        model2 = cleaned_data.get('model2')
        if model1 and model2 and model1 == model2:
            self.add_error('model2', "Lane 2 cannot have the same driver as Lane 1.")
        return cleaned_data
