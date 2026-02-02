from django import forms
from .models import Club, ClubLocation, ClubMember
from django.core.exceptions import ValidationError

class ClubForm(forms.ModelForm):
    class Meta:
        model = Club
        fields = ["display_name", "is_active"]

    def __init__(self, *args, **kwargs):
        self.owner = kwargs.pop("owner", None)
        super().__init__(*args, **kwargs)
        if self.owner and not self.instance.pk:
            self.instance.owner = self.owner

    def clean(self):
        cleaned_data = super().clean()
        try:
            self.instance.validate_unique()
        except ValidationError as e:
            raise forms.ValidationError(e)
        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.owner:
            instance.owner = self.owner
        if commit:
            instance.save()
        return instance

class ClubLocationForm(forms.ModelForm):
    class Meta:
        model = ClubLocation
        fields = ["location"]

    def __init__(self, *args, **kwargs):
        self.club = kwargs.pop("club", None)
        super().__init__(*args, **kwargs)
        if self.club:
            self.instance.club = self.club

    def clean(self):
        cleaned_data = super().clean()
        if not self.club or not cleaned_data.get("location"):
            return cleaned_data
        exists = ClubLocation.objects.filter(
            club=self.club,
            location=cleaned_data["location"])
        if self.instance.pk:
            exists = exists.exclude(pk=self.instance.pk)
        if exists.exists():
            raise forms.ValidationError("This club already has this location.")
        return cleaned_data

class ClubMemberForm(forms.ModelForm):
    class Meta:
        model = ClubMember
        fields = ["user", "role"]

    def __init__(self, *args, **kwargs):
        self.club = kwargs.pop("club", None)
        super().__init__(*args, **kwargs)
        if self.club:
            self.instance.club = self.club
    
    def clean(self):
        cleaned_data = super().clean()
        if not self.club or not cleaned_data.get("user"):
            return cleaned_data
        exists = ClubMember.objects.filter(
            club=self.club,
            user=cleaned_data["user"])
        if self.instance.pk:
            exists = exists.exclude(pk=self.instance.pk)

        if exists.exists():
            raise forms.ValidationError(
                "This user is already a member of this club."
            )

        return cleaned_data
