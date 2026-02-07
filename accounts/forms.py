from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django import forms
from django.contrib.auth.models import User
from .models import UserProfile

class RegisterForm(UserCreationForm):
    phone_number = forms.CharField(
        required=False,
        label="Phone Number",
        widget=forms.TextInput(attrs={"placeholder": "555-123-9999"}))
    
    class Meta:
        model = User
        fields = ("username", "first_name", "last_name", "email", "phone_number", "password1", "password2")

    def save(self, commit=True):
        user = super().save(commit)
        phone = self.cleaned_data.get("phone_number", "")
        profile, created = UserProfile.objects.get_or_create(user=user)
        profile.phone_number = phone
        if commit:
            profile.save()
        return user

class UserEditForm(forms.ModelForm):
    phone_number = forms.CharField(required=False, label="Phone Number")
    sms_opt_in = forms.BooleanField(required=False, label="SMS Opt-In")

    class Meta:
        model = User
        fields = ["username", "first_name", "last_name", "email"]

    def __init__(self, *args, **kwargs):
        user = kwargs.get("instance")
        super().__init__(*args, **kwargs)
        if user and hasattr(user, "profile"):
            self.fields["phone_number"].initial = user.profile.phone_number
            self.fields["sms_opt_in"].initial = user.profile.sms_opt_in

    def save(self, commit=True):
        user = super().save(commit)
        profile = user.profile
        profile.phone_number = self.cleaned_data.get("phone_number")
        profile.sms_opt_in = self.cleaned_data.get("sms_opt_in")
        if commit:
            profile.save()
        return user