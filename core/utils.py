from decimal import Decimal, InvalidOperation

from .models import AuditLog, Notification


def to_decimal(value, default=Decimal("0.00")):
    try:
        return Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        return default


def create_notification(user, title, message, notification_type="info", action_url=""):
    return Notification.objects.create(
        user=user,
        title=title,
        message=message,
        notification_type=notification_type,
        action_url=action_url,
    )


def record_audit(user, module, action, description="", object_type="", object_id="", metadata=None):
    return AuditLog.objects.create(
        user=user,
        module=module,
        action=action,
        description=description,
        object_type=object_type,
        object_id=str(object_id) if object_id else "",
        metadata=metadata or {},
    )
