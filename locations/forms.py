from decimal import Decimal, ROUND_HALF_UP

from django import forms
from django.forms import ModelForm
from .models import Location


class RoundedDecimalField(forms.DecimalField):
    """
    Same idea as Location.clean_fields()/clean() in models.py (round pasted
    coordinates down to decimal_places instead of rejecting them) but applied
    in to_python(), which runs before forms.DecimalField.validate() checks
    decimal_places. A plain ModelForm field validates precision on the raw
    input first, so a 15-digit lat/lon copy-pasted from Google Maps was
    rejected before the model ever got a chance to round it.
    """

    def to_python(self, value):
        value = super().to_python(value)
        if value is not None:
            value = value.quantize(
                Decimal(1).scaleb(-self.decimal_places),
                rounding=ROUND_HALF_UP,
            )
        return value


class LocationForm(ModelForm):
    latitude = RoundedDecimalField(
        max_digits=9,
        decimal_places=6,
        required=False,
        widget=forms.NumberInput(attrs={"step": "0.000001", "placeholder": "e.g. 34.052235"}),
    )
    longitude = RoundedDecimalField(
        max_digits=9,
        decimal_places=6,
        required=False,
        widget=forms.NumberInput(attrs={"step": "0.000001", "placeholder": "-118.243683"}),
    )

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
            "zip": forms.TextInput(attrs={"placeholder": "Postal code"})}

    def clean(self):
        cleaned_data = super().clean()
        lat = cleaned_data.get("latitude")
        lon = cleaned_data.get("longitude")
        if (lat is None) ^ (lon is None):
            raise forms.ValidationError("Latitude and longitude must both be provided.")
        return cleaned_data
