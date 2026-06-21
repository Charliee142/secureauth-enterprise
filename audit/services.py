from .models import AuditLog


class AuditService:
    @staticmethod
    def log(event_type, user=None, actor=None, request=None, metadata=None):
        ip = None
        user_agent = ""
        if request is not None:
            xff = request.META.get("HTTP_X_FORWARDED_FOR")
            ip = xff.split(",")[0].strip() if xff else request.META.get("REMOTE_ADDR")
            user_agent = request.META.get("HTTP_USER_AGENT", "")
            if actor is None and request.user.is_authenticated:
                actor = request.user

        return AuditLog.objects.create(
            user=user,
            actor=actor,
            event_type=event_type,
            ip_address=ip,
            user_agent=user_agent,
            metadata=metadata or {},
        )
