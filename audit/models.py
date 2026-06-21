from django.conf import settings
from django.db import models


class AuditLog(models.Model):
    EVENT_CHOICES = [
        ("REGISTRATION", "Registration"),
        ("EMAIL_VERIFIED", "Email Verified"),
        ("LOGIN_SUCCESS", "Login Success"),
        ("LOGIN_FAILURE", "Login Failure"),
        ("LOGOUT", "Logout"),
        ("ACCOUNT_LOCKOUT", "Account Lockout"),
        ("PASSWORD_RESET_REQUESTED", "Password Reset Requested"),
        ("PASSWORD_RESET_COMPLETED", "Password Reset Completed"),
        ("PASSWORD_CHANGED", "Password Changed"),
        ("ROLE_CHANGE", "Role Change"),
        ("OAUTH_LOGIN", "OAuth Login"),
        ("ADMIN_USER_DEACTIVATED", "Admin User Deactivated"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="audit_events",
    )
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="audit_actions",
    )
    event_type = models.CharField(max_length=50, choices=EVENT_CHOICES, db_index=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["user", "created_at"])]

    def __str__(self):
        return f"{self.event_type} @ {self.created_at}"
