from django.contrib import admin

from .models import AuditLog, Notification, SystemSetting


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("user", "title", "notification_type", "is_read", "created_at")
    list_filter = ("notification_type", "is_read")
    search_fields = ("user__username", "user__email", "title", "message")


@admin.register(SystemSetting)
class SystemSettingAdmin(admin.ModelAdmin):
    list_display = ("key", "value", "is_active", "updated_at")
    list_filter = ("is_active",)
    search_fields = ("key", "description")


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ("module", "action", "user", "created_at")
    list_filter = ("module", "action")
    search_fields = ("description", "object_id", "user__username")
