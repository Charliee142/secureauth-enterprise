from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import EmailVerification, LoginAttempt, PasswordResetToken, SessionRecord, User


class UserAdmin(BaseUserAdmin):
    model = User
    list_display = ("email", "username", "is_active", "is_email_verified", "is_staff", "date_joined")
    ordering = ("-date_joined",)
    fieldsets = (
        (None, {"fields": ("email", "username", "password")}),
        ("Status", {"fields": ("is_active", "is_email_verified", "is_staff", "is_superuser")}),
        ("Permissions", {"fields": ("groups", "user_permissions")}),
        ("Important dates", {"fields": ("last_login", "date_joined", "last_reauth_at")}),
    )
    add_fieldsets = (
        (None, {"fields": ("email", "username", "password1", "password2")}),
    )
    search_fields = ("email", "username")


admin.site.register(User, UserAdmin)
admin.site.register(EmailVerification)
admin.site.register(PasswordResetToken)
admin.site.register(LoginAttempt)
admin.site.register(SessionRecord)
