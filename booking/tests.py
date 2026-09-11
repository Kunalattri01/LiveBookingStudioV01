from django.contrib.auth import get_user_model
from django.test import TestCase

from .models import Booking, BookingItem
from .services import make_booking_reference


class BookingTests(TestCase):
    def test_booking_reference_is_unique(self):
        self.assertTrue(make_booking_reference().startswith("TRV-"))

    def test_booking_can_have_items(self):
        user = get_user_model().objects.create_user(username="demo", password="pass-12345")
        booking = Booking.objects.create(
            user=user,
            reference=make_booking_reference(),
            booking_type="flight",
            total_amount="5000.00",
        )
        BookingItem.objects.create(booking=booking, item_type="fare", name="Economy", unit_price="5000.00")
        self.assertEqual(booking.items.count(), 1)


class BookingApiTests(TestCase):
    def test_booking_api_only_returns_current_users_bookings(self):
        User = get_user_model()
        user = User.objects.create_user(username="one", password="StrongPass123!")
        other = User.objects.create_user(username="two", password="StrongPass123!")
        Booking.objects.create(user=user, reference=make_booking_reference(), booking_type="flight")
        Booking.objects.create(user=other, reference=make_booking_reference(), booking_type="hotel")
        self.client.force_login(user)
        response = self.client.get("/api/v1/booking/bookings/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 1)
