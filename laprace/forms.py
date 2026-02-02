from django import forms
from races.models import Race

class LapMonitorUploadForm(forms.Form):
    race = forms.ModelChoiceField(queryset=Race.objects.all())
    csv_file = forms.FileField()
