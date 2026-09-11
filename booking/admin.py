from django.contrib import admin

from .models import Booking, BookingItem, PaymentTransaction


class BookingItemInline(admin.TabularInline):
    model = BookingItem
    extra = 0


class PaymentInline(admin.TabularInline):
    model = PaymentTransaction
    extra = 0
    readonly_fields = ("created_at", "updated_at")


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ("reference", "user", "booking_type", "status", "total_amount", "currency", "created_at")
    list_filter = ("booking_type", "status", "currency")
    search_fields = ("reference", "supplier_reference", "user__username", "user__email")
    inlines = [BookingItemInline, PaymentInline]


@admin.register(PaymentTransaction)
class PaymentTransactionAdmin(admin.ModelAdmin):
    list_display = ("transaction_id", "booking", "status", "amount", "currency", "created_at")
    list_filter = ("status", "provider", "payment_method")
    search_fields = ("transaction_id", "provider_reference", "booking__reference")
