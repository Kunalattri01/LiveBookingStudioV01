from django.urls import path
from .views import *

urlpatterns = [
    path('', HotelView.as_view(), name='HotelPage'),
    path('search/', HotelSearchView.as_view(), name='HotelSearchPage'),
    path('hotel-listing/', HotelListingView.as_view(), name='HotelListingPage'),
    path('hotel-booking/', HotelBookingView.as_view(), name='HotelBookingPage'),
    path('hotel-confirmation/', HotelConfirmationView.as_view(), name='HotelConfirmationPage'),
    path('hotel-detail/', HotelDetailView.as_view(), name='HotelDetailPage'),
] 