from functools import wraps

from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect
from django.urls import reverse

from .models import Role, RoleAssignment


class RBACService:
    @staticmethod
    def get_role(user):
        return user.role

    @staticmethod
    def has_permission(user, codename):
        role = user.role
        if not role:
            return False
        return role.role_permissions.filter(permission__codename=codename).exists()

    @staticmethod
    def assign_role(target_user, role_name, acting_user):
        role = Role.objects.get(name=role_name)

        # Last-Administrator protection
        if target_user.has_role(Role.ADMINISTRATOR) and role_name != Role.ADMINISTRATOR:
            admin_count = RoleAssignment.objects.filter(
                role__name=Role.ADMINISTRATOR
            ).values("user").distinct().count()
            if admin_count <= 1:
                raise ValueError("Cannot remove the last remaining Administrator.")

        RoleAssignment.objects.create(user=target_user, role=role, assigned_by=acting_user)
        return role


def role_required(*role_names):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped(request, *args, **kwargs):
            if not request.user.is_authenticated or not request.user.has_role(*role_names):
                messages.error(request, "You do not have permission to access this page.")
                raise PermissionDenied("Insufficient role.")
            return view_func(request, *args, **kwargs)
        return _wrapped
    return decorator


def permission_required(codename):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped(request, *args, **kwargs):
            if not request.user.is_authenticated or not RBACService.has_permission(request.user, codename):
                messages.error(request, "You do not have permission to access this page.")
                raise PermissionDenied("Insufficient permission.")
            return view_func(request, *args, **kwargs)
        return _wrapped
    return decorator


def reauth_required(view_func):
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        if request.user.is_authenticated and request.user.needs_reauth():
            return redirect(f"{reverse('accounts:reauthenticate')}?next={request.path}")
        return view_func(request, *args, **kwargs)
    return _wrapped
