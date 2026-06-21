from django.urls import path

from . import views

app_name = "dashboard"

urlpatterns = [
    path("", views.home, name="home"),
    path("users/", views.user_management, name="user_management"),
    path("users/<int:user_id>/assign-role/", views.assign_role, name="assign_role"),
    path("security/", views.security_dashboard, name="security_dashboard"),
    path("audit-logs/", views.audit_log_dashboard, name="audit_log_dashboard"),
]
