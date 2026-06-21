from django.urls import path

from . import views

app_name = "accounts"

urlpatterns = [
    path("register/", views.RegisterView.as_view(), name="register"),
    path("verify-email/<str:token>/", views.VerifyEmailView.as_view(), name="verify_email"),
    path("login/", views.LoginView.as_view(), name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("password-reset/", views.PasswordResetRequestView.as_view(), name="password_reset"),
    path(
        "password-reset/confirm/<str:token>/",
        views.PasswordResetConfirmView.as_view(),
        name="password_reset_confirm",
    ),
    path("password-change/", views.password_change_view, name="password_change"),
    path("reauthenticate/", views.reauthenticate_view, name="reauthenticate"),
]
