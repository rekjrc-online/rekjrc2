from django import forms
from .models import Store

class StoreForm(forms.ModelForm):
    class Meta:
        model = Store
        fields = [
            'display_name',
            'is_active',
            'location',
            'description',
            'website',
            'email',
            'phone_number',
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
            'website': forms.URLInput(),
            'email': forms.EmailInput(),
            'phone_number': forms.TextInput(),
        }