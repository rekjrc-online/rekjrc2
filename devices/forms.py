from django import forms
from .models import Device


class DeviceForm(forms.ModelForm):
    class Meta:
        model = Device
        fields = ['mac', 'name', 'description', 'owner_team']
        widgets = {
            'mac': forms.TextInput(attrs={'placeholder': 'AA:BB:CC:DD:EE:FF'}),
            'name': forms.TextInput(attrs={'placeholder': 'Enter device name'}),
            'description': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Optional description'}),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        if user is not None:
            # Restrict owner_team to teams the user belongs to or owns
            from teams.models import Team
            from django.db.models import Q
            self.fields['owner_team'].queryset = Team.objects.filter(
                Q(owner=user) | Q(members__user=user)
            ).distinct()
            self.fields['owner_team'].required = False
