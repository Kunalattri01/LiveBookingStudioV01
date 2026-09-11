from django.urls import path
from .views import FlightView, AirportSearchView, FlightResultsView, FlightFareView, TravellerView, SeatSelectionView
from .views.vw_booking_review import BookingReviewView


urlpatterns = [
    path('', FlightView.as_view(), name='FlightPage'),
    path('airports/', AirportSearchView.as_view(), name='FlightAirportSearch'),
    path('results/', FlightResultsView.as_view(), name='FlightResultsPage'),
    path('flight-fare/', FlightFareView.as_view(), name='FlightFarePage'),
    path('traveller/', TravellerView.as_view(), name='TravellerPage'),
    path('seat-selection/', SeatSelectionView.as_view(), name='SeatSelectionPage'),
    path('review/', BookingReviewView.as_view(), name='BookingReviewPage'),
]