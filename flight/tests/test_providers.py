from django.test import TestCase, override_settings

from flight.providers.manager import SupplierManager
from flight.providers.mock_provider import MockFlightProvider
from flight.providers.tripjack_provider import TripJackAdapter
from flight.providers.unconfigured_provider import UnconfiguredProvider


class SupplierManagerSafetyTests(TestCase):
    """
    These tests exist specifically to prove the provider-safety
    requirement: no FLIGHT_PROVIDER value can ever select the mock
    provider, and any non-"tripjack" value is safe.
    """

    @override_settings(FLIGHT_PROVIDER="unconfigured")
    def test_unconfigured_resolves_to_unconfigured_provider(self):
        provider = SupplierManager.get_provider()
        self.assertIsInstance(provider, UnconfiguredProvider)

    @override_settings(FLIGHT_PROVIDER="")
    def test_empty_value_resolves_to_unconfigured_provider(self):
        provider = SupplierManager.get_provider()
        self.assertIsInstance(provider, UnconfiguredProvider)

    @override_settings(FLIGHT_PROVIDER="mock")
    def test_mock_is_not_a_selectable_provider(self):
        """
        Setting FLIGHT_PROVIDER=mock must NOT return MockFlightProvider.
        It must fall through to the safe default, exactly like any
        other unrecognized value.
        """
        provider = SupplierManager.get_provider()
        self.assertNotIsInstance(provider, MockFlightProvider)
        self.assertIsInstance(provider, UnconfiguredProvider)

    @override_settings(FLIGHT_PROVIDER="some-typo-value")
    def test_unknown_value_resolves_to_unconfigured_provider(self):
        provider = SupplierManager.get_provider()
        self.assertIsInstance(provider, UnconfiguredProvider)

    @override_settings(FLIGHT_PROVIDER="tripjack")
    def test_tripjack_value_resolves_to_tripjack_adapter(self):
        provider = SupplierManager.get_provider()
        self.assertIsInstance(provider, TripJackAdapter)

    def test_mock_provider_is_never_imported_by_manager_module(self):
        import flight.providers.manager as manager_module

        source = open(manager_module.__file__).read()
        self.assertNotIn("import MockFlightProvider", source)
        self.assertNotIn("mock_provider", source)
        self.assertNotIn("\"mock\":", source)
        self.assertNotIn("'mock':", source)
