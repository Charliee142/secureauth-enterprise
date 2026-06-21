from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login as auth_login, logout as auth_login_out
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.shortcuts import redirect, render
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone
from django.views import View

from audit.services import AuditService
from .forms import (
    LoginForm,
    PasswordChangeForm,
    PasswordResetConfirmForm,
    PasswordResetRequestForm,
    RegistrationForm,
)
from .models import EmailVerification, LoginAttempt, PasswordResetToken, SessionRecord, User


def _client_ip(request):
    xff = request.META.get("HTTP_X_FORWARDED_FOR")
    if xff:
        return xff.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")


def _is_locked_out(identifier):
    threshold = settings.ACCOUNT_LOCKOUT_THRESHOLD
    cooldown = settings.ACCOUNT_LOCKOUT_COOLDOWN_SECONDS
    window_start = timezone.now() - timezone.timedelta(seconds=cooldown)
    recent = LoginAttempt.objects.filter(identifier=identifier, created_at__gte=window_start)
    failures = recent.filter(successful=False).count()
    last_success = recent.filter(successful=True).order_by("-created_at").first()
    if last_success:
        # only count failures after the last success
        failures = recent.filter(successful=False, created_at__gt=last_success.created_at).count()
    return failures >= threshold


class RegisterView(View):
    template_name = "accounts/register.html"

    def get(self, request):
        return render(request, self.template_name, {"form": RegistrationForm()})

    def post(self, request):
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = User.objects.create_user(
                email=form.cleaned_data["email"],
                username=form.cleaned_data["username"],
                password=form.cleaned_data["password"],
            )
            verification = EmailVerification.objects.create(user=user)
            verify_url = request.build_absolute_uri(
                reverse("accounts:verify_email", args=[verification.token])
            )
            send_mail(
                "Verify your SecureAuth Enterprise account",
                f"Click to verify your account: {verify_url}",
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
                fail_silently=True,
            )
            AuditService.log("REGISTRATION", user=user, request=request)
            return render(request, "accounts/registration_pending.html", {"email": user.email})
        return render(request, self.template_name, {"form": form})


class VerifyEmailView(View):
    def get(self, request, token):
        try:
            verification = EmailVerification.objects.select_related("user").get(token=token)
        except EmailVerification.DoesNotExist:
            messages.error(request, "Invalid verification link.")
            return redirect("accounts:login")

        if not verification.is_valid():
            messages.error(request, "This verification link has expired or was already used.")
            return redirect("accounts:login")

        user = verification.user
        user.is_active = True
        user.is_email_verified = True
        user.save(update_fields=["is_active", "is_email_verified"])
        verification.used = True
        verification.save(update_fields=["used"])

        from rbac.models import Role, RoleAssignment
        if not RoleAssignment.objects.filter(user=user).exists():
            default_role, _ = Role.objects.get_or_create(name=Role.USER)
            RoleAssignment.objects.create(user=user, role=default_role)

        AuditService.log("EMAIL_VERIFIED", user=user, request=request)
        messages.success(request, "Your email has been verified. You may now log in.")
        return redirect("accounts:login")


class LoginView(View):
    template_name = "accounts/login.html"

    def get(self, request):
        return render(request, self.template_name, {"form": LoginForm()})

    def post(self, request):
        form = LoginForm(request.POST)
        if not form.is_valid():
            return render(request, self.template_name, {"form": form})

        identifier = form.cleaned_data["identifier"]
        password = form.cleaned_data["password"]
        ip = _client_ip(request)

        if _is_locked_out(identifier):
            AuditService.log("ACCOUNT_LOCKOUT", request=request, metadata={"identifier": identifier})
            messages.error(
                request,
                "This account is temporarily locked due to multiple failed login attempts. "
                "Please try again later or reset your password.",
            )
            return render(request, self.template_name, {"form": form})

        user_obj = User.objects.filter(email__iexact=identifier).first() or \
            User.objects.filter(username__iexact=identifier).first()

        user = None
        if user_obj:
            user = authenticate(request, username=user_obj.email, password=password)

        if user is None:
            LoginAttempt.objects.create(identifier=identifier, ip_address=ip, successful=False)
            AuditService.log(
                "LOGIN_FAILURE", request=request, metadata={"identifier": identifier}
            )
            messages.error(request, "Invalid credentials.")
            return render(request, self.template_name, {"form": form})

        if not user.is_email_verified:
            messages.error(request, "Please verify your email before logging in.")
            return render(request, self.template_name, {"form": form})

        LoginAttempt.objects.create(identifier=identifier, ip_address=ip, successful=True)
        auth_login(request, user)
        user.mark_reauthenticated()
        request.session["_last_activity"] = timezone.now().timestamp()
        SessionRecord.objects.update_or_create(
            session_key=request.session.session_key or request.session._get_or_create_session_key(),
            defaults={
                "user": user,
                "ip_address": ip,
                "user_agent": request.META.get("HTTP_USER_AGENT", ""),
                "expired": False,
            },
        )
        AuditService.log("LOGIN_SUCCESS", user=user, request=request)
        return redirect(settings.LOGIN_REDIRECT_URL)


@login_required
def logout_view(request):
    user = request.user
    SessionRecord.objects.filter(session_key=request.session.session_key).update(expired=True)
    AuditService.log("LOGOUT", user=user, request=request)
    auth_login_out(request)
    messages.success(request, "You have been logged out.")
    return redirect("accounts:login")


class PasswordResetRequestView(View):
    template_name = "accounts/password_reset_request.html"

    def get(self, request):
        return render(request, self.template_name, {"form": PasswordResetRequestForm()})

    def post(self, request):
        form = PasswordResetRequestForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data["email"]
            user = User.objects.filter(email__iexact=email).first()
            if user:
                token = PasswordResetToken.objects.create(user=user)
                reset_url = request.build_absolute_uri(
                    reverse("accounts:password_reset_confirm", args=[token.token])
                )
                send_mail(
                    "Reset your SecureAuth Enterprise password",
                    f"Click to reset your password: {reset_url}",
                    settings.DEFAULT_FROM_EMAIL,
                    [user.email],
                    fail_silently=True,
                )
                AuditService.log("PASSWORD_RESET_REQUESTED", user=user, request=request)
            # Always show the same generic message (anti-enumeration)
            return render(request, "accounts/password_reset_sent.html")
        return render(request, self.template_name, {"form": form})


class PasswordResetConfirmView(View):
    template_name = "accounts/password_reset_confirm.html"

    def get(self, request, token):
        return render(request, self.template_name, {"form": PasswordResetConfirmForm(), "token": token})

    def post(self, request, token):
        form = PasswordResetConfirmForm(request.POST)
        try:
            reset_token = PasswordResetToken.objects.select_related("user").get(token=token)
        except PasswordResetToken.DoesNotExist:
            messages.error(request, "Invalid or expired reset link.")
            return redirect("accounts:login")

        if not reset_token.is_valid():
            messages.error(request, "This reset link has expired or was already used.")
            return redirect("accounts:login")

        if form.is_valid():
            user = reset_token.user
            user.set_password(form.cleaned_data["new_password"])
            user.save(update_fields=["password"])
            reset_token.used = True
            reset_token.save(update_fields=["used"])
            # Invalidate all existing sessions for this user
            SessionRecord.objects.filter(user=user, expired=False).update(expired=True)
            AuditService.log("PASSWORD_RESET_COMPLETED", user=user, request=request)
            messages.success(request, "Your password has been reset. Please log in again.")
            return redirect("accounts:login")
        return render(request, self.template_name, {"form": form, "token": token})


@login_required
def password_change_view(request):
    if request.method == "POST":
        form = PasswordChangeForm(request.POST, user=request.user)
        if form.is_valid():
            request.user.set_password(form.cleaned_data["new_password"])
            request.user.save(update_fields=["password"])
            request.user.mark_reauthenticated()
            AuditService.log("PASSWORD_CHANGED", user=request.user, request=request)
            messages.success(request, "Password changed successfully.")
            return redirect("dashboard:home")
    else:
        form = PasswordChangeForm(user=request.user)
    return render(request, "accounts/password_change.html", {"form": form})


@login_required
def reauthenticate_view(request):
    """Forces password re-entry before sensitive actions (SEC-004)."""
    next_url = request.GET.get("next") or request.POST.get("next") or "dashboard:home"
    if request.method == "POST":
        password = request.POST.get("password", "")
        if request.user.check_password(password):
            request.user.mark_reauthenticated()
            messages.success(request, "Re-authentication successful.")
            return redirect(next_url)
        messages.error(request, "Incorrect password.")
    return render(request, "accounts/reauthenticate.html", {"next": next_url})
