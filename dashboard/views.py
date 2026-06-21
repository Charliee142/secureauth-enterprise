from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from accounts.models import LoginAttempt, SessionRecord, User
from audit.models import AuditLog
from audit.services import AuditService
from rbac.models import Role, RoleAssignment
from rbac.services import RBACService, reauth_required, role_required


@login_required
def home(request):
    context = {
        "active_sessions": SessionRecord.objects.filter(expired=False).count(),
        "failed_logins_24h": LoginAttempt.objects.filter(
            successful=False, created_at__gte=timezone.now() - timezone.timedelta(hours=24)
        ).count(),
        "locked_accounts": 0,
        "admins": RoleAssignment.objects.filter(role__name=Role.ADMINISTRATOR).values("user").distinct().count(),
        "recent_events": AuditLog.objects.select_related("user", "actor")[:10],
        "role": request.user.role,
    }
    return render(request, "dashboard/home.html", context)


@login_required
@role_required(Role.MODERATOR, Role.ADMINISTRATOR)
def user_management(request):
    users = User.objects.all().order_by("-date_joined")
    paginator = Paginator(users, 25)
    page_obj = paginator.get_page(request.GET.get("page"))
    return render(request, "dashboard/user_management.html", {"page_obj": page_obj, "roles": Role.objects.all()})


@login_required
@role_required(Role.ADMINISTRATOR)
@reauth_required
def assign_role(request, user_id):
    target = get_object_or_404(User, id=user_id)
    if request.method == "POST":
        role_name = request.POST.get("role")
        try:
            RBACService.assign_role(target, role_name, acting_user=request.user)
            AuditService.log(
                "ROLE_CHANGE",
                user=target,
                actor=request.user,
                request=request,
                metadata={"new_role": role_name},
            )
            messages.success(request, f"Updated {target.email}'s role to {role_name}.")
        except Exception as exc:
            messages.error(request, str(exc))
    return redirect("dashboard:user_management")


@login_required
@role_required(Role.ADMINISTRATOR)
@reauth_required
def security_dashboard(request):
    context = {
        "active_sessions": SessionRecord.objects.filter(expired=False).count(),
        "failed_logins_24h": LoginAttempt.objects.filter(
            successful=False, created_at__gte=timezone.now() - timezone.timedelta(hours=24)
        ).count(),
        "lockouts_24h": AuditLog.objects.filter(
            event_type="ACCOUNT_LOCKOUT", created_at__gte=timezone.now() - timezone.timedelta(hours=24)
        ).count(),
        "admins": RoleAssignment.objects.filter(role__name=Role.ADMINISTRATOR).values("user").distinct().count(),
        "recent_security_events": AuditLog.objects.filter(
            event_type__in=["LOGIN_FAILURE", "ACCOUNT_LOCKOUT", "ROLE_CHANGE", "PASSWORD_RESET_COMPLETED"]
        )[:25],
    }
    return render(request, "dashboard/security_dashboard.html", context)


@login_required
@role_required(Role.ADMINISTRATOR)
@reauth_required
def audit_log_dashboard(request):
    logs = AuditLog.objects.select_related("user", "actor").all()
    event_type = request.GET.get("event_type")
    if event_type:
        logs = logs.filter(event_type=event_type)
    paginator = Paginator(logs, 50)
    page_obj = paginator.get_page(request.GET.get("page"))
    return render(
        request,
        "dashboard/audit_log_dashboard.html",
        {"page_obj": page_obj, "event_choices": AuditLog.EVENT_CHOICES, "selected_event": event_type},
    )
