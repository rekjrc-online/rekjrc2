from django import forms
from .models import Driver

class DriverForm(forms.ModelForm):
    class Meta:
        model = Driver
        fields = [
            'display_name',
            'is_active',
        ]
        widgets = {
            'display_name': forms.TextInput(attrs={'placeholder': 'Enter driver name'}),
            'is_active': forms.CheckboxInput(),
        }
