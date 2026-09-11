from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .api import AuditLogViewSet, HealthApiView, NotificationViewSet, SystemSettingViewSet

router = DefaultRouter()
router.register("notifications", NotificationViewSet, basename="notification")
router.register("settings", SystemSettingViewSet, basename="setting")
router.register("audit-logs", AuditLogViewSet, basename="audit-log")

urlpatterns = [
    path("health/", HealthApiView.as_view(), name="health"),
    path("", include(router.urls)),
]
