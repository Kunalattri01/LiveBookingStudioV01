from django.urls import path

from .booking import (
    ApiFlightFareRule,
    FlightReviewApiView,
    FlightSeatMapApiView,
    FlightTravellerApiView,
    FlightSelectionApiView,
    FlightSeatSelectionApiView,
)
from .views import (
    AirportSearchApiView,
    FlightSearchApiView,
)


urlpatterns = [
    path("airports/", AirportSearchApiView.as_view(), name="ApiAirportSearch"),
    path("flights/search/", FlightSearchApiView.as_view(), name="ApiFlightSearch"),
    path("flights/selection/", FlightSelectionApiView.as_view(), name="ApiFlightSelection"),
    path("flights/review/", FlightReviewApiView.as_view(), name="ApiFlightReview"),
    path("flights/traveller/" , FlightTravellerApiView.as_view(), name="ApiFlightTraveller"),
    path("flights/seat-map/", FlightSeatMapApiView.as_view(), name="ApiFlightSeatMap"),
    path("flights/seat-selection/", FlightSeatSelectionApiView.as_view(), name="ApiFlightSeatSelection"),
    path("flights/fare-rule/", ApiFlightFareRule.as_view(), name="ApiFlightFareRule"),
]
