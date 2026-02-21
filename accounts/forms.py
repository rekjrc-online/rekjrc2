from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import get_user_model
from django import forms
from .models import UserProfile

User = get_user_model()


class RegisterForm(UserCreationForm):
    # Explicitly remove the username field that UserCreationForm declares at class level
    username = None

    phone_number = forms.CharField(
        required=False,
        label="Phone Number",
        widget=forms.TextInput(attrs={"placeholder": "555-123-9999"}))

    class Meta:
        model = User
        fields = ("first_name", "last_name", "email", "phone_number", "password1", "password2")

    def clean_email(self):
        email = self.cleaned_data["email"].lower().strip()
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("An account with this email already exists.")
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.username = self.cleaned_data["email"]  # already lowercased by clean_email
        if commit:
            user.save()
        phone = self.cleaned_data.get("phone_number", "")
        user.profile.phone_number = phone
        if commit:
            user.profile.save()
        return user


class UserEditForm(forms.ModelForm):
    phone_number = forms.CharField(required=False, label="Phone Number")
    sms_opt_in = forms.BooleanField(required=False, label="SMS Opt-In")

    class Meta:
        model = User
        fields = ["first_name", "last_name", "email"]

    def __init__(self, *args, **kwargs):
        user = kwargs.get("instance")
        super().__init__(*args, **kwargs)
        if user and hasattr(user, "profile"):
            self.fields["phone_number"].initial = user.profile.phone_number
            self.fields["sms_opt_in"].initial = user.profile.sms_opt_in

    def clean_email(self):
        email = self.cleaned_data["email"].lower().strip()
        qs = User.objects.filter(email=email).exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError("An account with this email already exists.")
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.username = user.email  # already lowercased by clean_email
        if commit:
            user.save()
        profile = user.profile
        profile.phone_number = self.cleaned_data.get("phone_number")
        profile.sms_opt_in = self.cleaned_data.get("sms_opt_in")
        if commit:
            profile.save()
        return user


class EmailAuthForm(AuthenticationForm):
    """
    Login form that uses email instead of username.
    Declared at class level to guarantee the label regardless of Django version.
    """

    username = forms.EmailField(
        label="Email",
        widget=forms.EmailInput(attrs={"placeholder": "you@example.com", "autofocus": True}))

    def clean_username(self):
        return self.cleaned_data["username"].lower().strip()