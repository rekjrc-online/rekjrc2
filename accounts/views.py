import requests

from django.conf import settings
from django.contrib.auth import views as auth_views, get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import UpdateView, CreateView
from django.urls import reverse_lazy
from .forms import RegisterForm, UserEditForm, EmailAuthForm

User = get_user_model()

TURNSTILE_VERIFY_URL = "https://challenges.cloudflare.com/turnstile/v0/siteverify"

class AccountEditView(LoginRequiredMixin, UpdateView):
    model = User
    form_class = UserEditForm
    template_name = "accounts/account.html"
    success_url = reverse_lazy("accounts:account")

    def get_object(self):
        return self.request.user

class LoginView(auth_views.LoginView):
    template_name = "accounts/login.html"
    authentication_form = EmailAuthForm

class LogoutView(auth_views.LogoutView):
    pass

class PasswordChangeView(auth_views.PasswordChangeView):
    template_name = "accounts/password_change.html"

class PasswordChangeDoneView(auth_views.PasswordChangeDoneView):
    template_name = "accounts/password_change_done.html"

class PasswordResetView(auth_views.PasswordResetView):
    template_name = "accounts/password_reset.html"
    email_template_name = "accounts/password_reset_email.html"
    subject_template_name = "accounts/password_reset_subject.txt"

class PasswordResetDoneView(auth_views.PasswordResetDoneView):
    template_name = "accounts/password_reset_done.html"

class PasswordResetConfirmView(auth_views.PasswordResetConfirmView):
    template_name = "accounts/password_reset_confirm.html"

class PasswordResetCompleteView(auth_views.PasswordResetCompleteView):
    template_name = "accounts/password_reset_complete.html"

class RegisterView(CreateView):
    model = User
    form_class = RegisterForm
    template_name = "accounts/register.html"
    success_url = reverse_lazy("accounts:login")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["turnstile_site_key"] = settings.TURNSTILE_SITE_KEY
        return context

    def form_valid(self, form):
        if not self._verify_turnstile():
            form.add_error(None, "Captcha verification failed. Please try again.")
            return self.form_invalid(form)
        return super().form_valid(form)

    def _verify_turnstile(self):
        token = self.request.POST.get("cf-turnstile-response", "")
        if not settings.TURNSTILE_SECRET_KEY:
            return True  # captcha disabled if not configured
        if not token:
            return False
        try:
            resp = requests.post(
                TURNSTILE_VERIFY_URL,
                data={
                    "secret": settings.TURNSTILE_SECRET_KEY,
                    "response": token,
                    "remoteip": self.request.META.get("REMOTE_ADDR", ""),
                },
                timeout=5,
            )
            return resp.json().get("success", False)
        except requests.RequestException:
            return False