from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .api import BookingViewSet, PaymentTransactionViewSet

router = DefaultRouter()
router.register("bookings", BookingViewSet, basename="booking")
router.register("payments", PaymentTransactionViewSet, basename="payment")

urlpatterns = [path("", include(router.urls))]
