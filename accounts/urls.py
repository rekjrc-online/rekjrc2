from django.urls import path
from django.contrib.auth import views as auth_views
from .views import AccountEditView, RegisterView, LoginView

app_name = "accounts"

urlpatterns = [
    path("",
         AccountEditView.as_view(),
         name="account"),

    path("login/",
        LoginView.as_view(),
        name="login"),

    path("logout/",
        auth_views.LogoutView.as_view(),
        name="logout"),

    path("register/",
         RegisterView.as_view(),
         name="register"),

    path("password-change/",
        auth_views.PasswordChangeView.as_view(
            template_name="accounts/password_change.html"),
        name="password_change"),

    path("password-change/done/",
        auth_views.PasswordChangeDoneView.as_view(
            template_name="accounts/password_change_done.html"),
        name="password_change_done"),

    path("password-reset/",
        auth_views.PasswordResetView.as_view(
            template_name=          "accounts/password_reset.html",
            email_template_name=    "accounts/password_reset_email.html",
            subject_template_name=  "accounts/password_reset_subject.txt"),
        name="password_reset"),

    path("password-reset/done/",
        auth_views.PasswordResetDoneView.as_view(
            template_name="accounts/password_reset_done.html"),
        name="password_reset_done"),

    path("reset/<uidb64>/<token>/",
        auth_views.PasswordResetConfirmView.as_view(
            template_name="accounts/password_reset_confirm.html"),
        name="password_reset_confirm"),

    path("reset/done/",
        auth_views.PasswordResetCompleteView.as_view(
            template_name="accounts/password_reset_complete.html"),
        name="password_reset_complete"),
]