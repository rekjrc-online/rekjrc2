from django import forms
from django.forms import ModelForm
from .models import Location

class LocationForm(ModelForm):
    class Meta:
        model = Location
        fields = [
            "display_name",
            "address1",
            "address2",
            "city",
            "state",
            "zip",
            "latitude",
            "longitude",
            "is_active" ]
        widgets = {
            "display_name": forms.TextInput(attrs={"placeholder": "Location name"}),
            "address1": forms.TextInput(attrs={"placeholder": "Address line 1"}),
            "address2": forms.TextInput(attrs={"placeholder": "Address line 2"}),
            "city": forms.TextInput(attrs={"placeholder": "City"}),
            "state": forms.TextInput(attrs={"placeholder": "State / Province"}),
            "zip": forms.TextInput(attrs={"placeholder": "Postal code"}),
            "latitude": forms.NumberInput(attrs={"step": "0.000001", "placeholder": "e.g. 34.052235"}),
            "longitude": forms.NumberInput(attrs={"step": "0.000001", "placeholder": "-118.243683"})}

    def clean(self):
        cleaned_data = super().clean()
        lat = cleaned_data.get("latitude")
        lon = cleaned_data.get("longitude")
        if (lat is None) ^ (lon is None):
            raise forms.ValidationError("Latitude and longitude must both be provided.")
        return cleaned_data
