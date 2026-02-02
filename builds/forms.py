from django import forms
from .models import Build, ATTRIBUTE_NAMES

class BuildForm(forms.ModelForm):
    class Meta:
        model = Build
        fields = ['display_name','year','make','model','is_active']
        fields = (fields + ATTRIBUTE_NAMES)

    def __init__(self, *args, **kwargs):
        self.owner = kwargs.pop('owner', None)
        super().__init__(*args, **kwargs)

    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.owner and not instance.pk:
            instance.owner = self.owner
        if commit:
            instance.save()
        return instance
