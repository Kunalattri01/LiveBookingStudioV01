from django.test import SimpleTestCase, override_settings

from hotel.providers.booking_manager import BookingSupplierManager
from hotel.providers.exceptions import ProviderNotConfiguredError
from hotel.providers.manager import SupplierManager
from hotel.providers.tripjack_booking_provider import TripJackHotelBookingAdapter
from hotel.providers.tripjack_provider import TripJackHotelAdapter
from hotel.providers.unconfigured_provider import UnconfiguredHotelProvider


class SupplierManagerSafetyTests(SimpleTestCase):
    """
    These tests exist specifically to prove HOTEL_PROVIDER can never
    silently select real hotel data when it isn't actually configured.
    """

    @override_settings(HOTEL_PROVIDER="unconfigured")
    def test_unconfigured_value_returns_unconfigured_provider(self):
        self.assertIsInstance(SupplierManager.get_provider(), UnconfiguredHotelProvider)

    @override_settings(HOTEL_PROVIDER="not-a-real-provider")
    def test_unrecognized_value_defaults_to_unconfigured_provider(self):
        self.assertIsInstance(SupplierManager.get_provider(), UnconfiguredHotelProvider)

    @override_settings(HOTEL_PROVIDER="tripjack")
    def test_tripjack_value_returns_tripjack_adapter(self):
        self.assertIsInstance(SupplierManager.get_provider(), TripJackHotelAdapter)

    @override_settings(HOTEL_PROVIDER="TripJack")
    def test_provider_name_is_case_insensitive(self):
        self.assertIsInstance(SupplierManager.get_provider(), TripJackHotelAdapter)


class BookingSupplierManagerSafetyTests(SimpleTestCase):
    @override_settings(HOTEL_PROVIDER="unconfigured")
    def test_unconfigured_raises_instead_of_returning_null_object(self):
        with self.assertRaises(ProviderNotConfiguredError):
            BookingSupplierManager.get_provider()

    @override_settings(HOTEL_PROVIDER="tripjack")
    def test_tripjack_value_returns_tripjack_booking_adapter(self):
        self.assertIsInstance(BookingSupplierManager.get_provider(), TripJackHotelBookingAdapter)
