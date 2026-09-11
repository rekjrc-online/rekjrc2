import requests

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import views as auth_views, get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect, render
from django.views.generic import UpdateView, CreateView, View
from django.urls import reverse_lazy
from .forms import RegisterForm, UserEditForm, EmailAuthForm
from .models import VerificationLog

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

class VerifiedRequiredMixin(LoginRequiredMixin):
    """
    Gates a view to logged-in users whose own Account.is_verified is True --
    used by the "Verify a Friend" flow, since only an already-verified user
    may verify someone else. Unverified (but logged-in) users are bounced to
    their own account page with an explanatory message instead of the normal
    LoginRequiredMixin login-page redirect, which is reserved for the
    logged-out case.
    """
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and not request.user.is_verified:
            messages.error(request, "Only verified accounts can verify other accounts.")
            return redirect("accounts:account")
        return super().dispatch(request, *args, **kwargs)

class VerifyFriendView(VerifiedRequiredMixin, View):
    """
    GET /accounts/verify/ -- camera-scan landing page for an already-verified
    user to scan another account's QR code (the same {"uuid": "...", "type":
    "user"} payload as accounts/account.html and events/checkin.html decode).
    The page itself just hosts the scanner; decoding happens client-side and
    hands off to VerifyConfirmView by uuid -- no server round-trip needed to
    read the code, same pattern as events/checkin.html's "Scan account QR".
    """
    def get(self, request, *args, **kwargs):
        return render(request, "accounts/verify.html")

class VerifyConfirmView(VerifiedRequiredMixin, View):
    """
    GET  /accounts/verify/confirm/<target_uuid>/ -- shows who's about to be
         verified and asks for an explicit confirm click.
    POST same URL -- performs the verification: sets the target account's
         is_verified True and writes one permanent VerificationLog row (see
         accounts.models.VerificationLog). Re-checks every rule at POST time
         too, not just GET, since the confirm page could otherwise be left
         open and submitted after something changed.
    """
    def _get_target(self, request, target_uuid):
        target = get_object_or_404(User, uuid=target_uuid)
        if target.pk == request.user.pk:
            messages.error(request, "You can't verify your own account.")
            return None
        return target

    def get(self, request, *args, **kwargs):
        target = self._get_target(request, kwargs["target_uuid"])
        if target is None:
            return redirect("accounts:verify")
        return render(request, "accounts/verify_confirm.html", {"target": target})

    def post(self, request, *args, **kwargs):
        target = self._get_target(request, kwargs["target_uuid"])
        if target is None:
            return redirect("accounts:verify")
        if target.is_verified:
            messages.info(request, f"{target.get_full_name() or target.email} is already verified.")
            return redirect("accounts:verify")

        target.is_verified = True
        target.save(update_fields=["is_verified"])

        VerificationLog.objects.create(
            verifier=request.user,
            verifier_uuid=request.user.uuid,
            verifier_email=request.user.email,
            verifier_name=request.user.get_full_name(),
            verified_user=target,
            verified_uuid=target.uuid,
            verified_email=target.email,
            verified_name=target.get_full_name(),
        )

        messages.success(request, f"You verified {target.get_full_name() or target.email}.")
        return redirect("accounts:account")