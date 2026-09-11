from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from core.utils import create_notification, record_audit
from .models import Booking, PaymentTransaction
from .serializers import BookingSerializer, PaymentTransactionSerializer


class BookingViewSet(viewsets.ModelViewSet):
    serializer_class = BookingSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Booking.objects.filter(user=self.request.user).prefetch_related("items", "payments")

    def perform_create(self, serializer):
        booking = serializer.save()
        record_audit(self.request.user, "booking", "created", "Booking created", "Booking", booking.reference)
        create_notification(self.request.user, "Booking created", f"Booking {booking.reference} has been created.", "success")

    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        booking = self.get_object()
        if booking.status in {"cancelled", "completed"}:
            return Response({"detail": "This booking cannot be cancelled."}, status=status.HTTP_400_BAD_REQUEST)
        booking.status = "cancelled"
        booking.save(update_fields=["status", "updated_at"])
        record_audit(request.user, "booking", "cancelled", "Booking cancelled", "Booking", booking.reference)
        create_notification(request.user, "Booking cancelled", f"Booking {booking.reference} has been cancelled.", "info")
        return Response(self.get_serializer(booking).data)


class PaymentTransactionViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = PaymentTransactionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return PaymentTransaction.objects.filter(booking__user=self.request.user)
