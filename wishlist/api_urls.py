from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .api import WishlistItemViewSet, WishlistViewSet

router = DefaultRouter()
router.register("lists", WishlistViewSet, basename="wishlist")
router.register("items", WishlistItemViewSet, basename="wishlist-item")

urlpatterns = [path("", include(router.urls))]
