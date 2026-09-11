from rest_framework import serializers

from .models import AuditLog, Notification, SystemSetting


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = [
            "id", "title", "message", "notification_type", "action_url",
            "is_read", "created_at", "read_at",
        ]
        read_only_fields = ["id", "created_at", "read_at"]


class SystemSettingSerializer(serializers.ModelSerializer):
    class Meta:
        model = SystemSetting
        fields = ["id", "key", "value", "description", "is_active", "updated_at"]
        read_only_fields = ["id", "updated_at"]


class AuditLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = AuditLog
        fields = [
            "id", "action", "module", "object_type", "object_id",
            "description", "metadata", "created_at",
        ]
        read_only_fields = fields
