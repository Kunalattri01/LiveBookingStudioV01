from django.db import connection
from rest_framework import permissions, status, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView
from django.utils import timezone

from .models import AuditLog, Notification, SystemSetting
from .serializers import AuditLogSerializer, NotificationSerializer, SystemSettingSerializer


class HealthApiView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        try:
            connection.ensure_connection()
            database_ok = True
        except Exception:
            database_ok = False
        code = status.HTTP_200_OK if database_ok else status.HTTP_503_SERVICE_UNAVAILABLE
        return Response({"status": "ok" if database_ok else "degraded", "database": database_ok, "time": timezone.now() }, status=code)


class NotificationViewSet(viewsets.ModelViewSet):
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ["get", "post", "patch", "head", "options"]

    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def perform_update(self, serializer):
        instance = serializer.save()
        if instance.is_read and instance.read_at is None:
            instance.read_at = timezone.now()
            instance.save(update_fields=["read_at"])


class SystemSettingViewSet(viewsets.ModelViewSet):
    queryset = SystemSetting.objects.filter(is_active=True)
    serializer_class = SystemSettingSerializer
    permission_classes = [permissions.IsAdminUser]


class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = AuditLog.objects.all()
    serializer_class = AuditLogSerializer
    permission_classes = [permissions.IsAdminUser]
