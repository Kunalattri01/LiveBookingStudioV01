from rest_framework import serializers

from .models import Booking, BookingItem, PaymentTransaction
from .services import make_booking_reference


class BookingItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = BookingItem
        fields = ["id", "item_type", "name", "description", "quantity", "unit_price", "metadata", "created_at"]
        read_only_fields = ["id", "created_at"]


class PaymentTransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentTransaction
        fields = [
            "id", "transaction_id", "provider", "payment_method", "status", "amount",
            "currency", "provider_reference", "failure_reason", "metadata", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "transaction_id", "created_at", "updated_at"]


class BookingSerializer(serializers.ModelSerializer):
    items = BookingItemSerializer(many=True, required=False)
    payments = PaymentTransactionSerializer(many=True, read_only=True)

    class Meta:
        model = Booking
        fields = [
            "id", "reference", "booking_type", "status", "supplier_name", "supplier_reference",
            "total_amount", "currency", "search_reference", "contact_name", "contact_email",
            "contact_phone", "metadata", "items", "payments", "created_at", "updated_at",
        ]
        read_only_fields = [
            "id", "reference", "status", "supplier_reference", "payments",
            "created_at", "updated_at",
        ]

    def create(self, validated_data):
        items = validated_data.pop("items", [])
        booking = Booking.objects.create(
            user=self.context["request"].user,
            reference=make_booking_reference(),
            **validated_data,
        )
        BookingItem.objects.bulk_create([BookingItem(booking=booking, **item) for item in items])
        return booking
