from django.urls import path

from .booking import HotelBookApiView, HotelBookingDetailsApiView, HotelReviewApiView
from .views import HotelDestinationSearchApiView, HotelListingApiView, HotelPricingApiView

urlpatterns = [
    path("hotels/destinations/", HotelDestinationSearchApiView.as_view(), name="ApiHotelDestinationSearch"),
    path("hotels/listing/", HotelListingApiView.as_view(), name="ApiHotelListing"),
    path("hotels/pricing/", HotelPricingApiView.as_view(), name="ApiHotelPricing"),
    path("hotels/review/", HotelReviewApiView.as_view(), name="ApiHotelReview"),
    path("hotels/book/", HotelBookApiView.as_view(), name="ApiHotelBook"),
    path("hotels/booking-details/", HotelBookingDetailsApiView.as_view(), name="ApiHotelBookingDetails"),
]
