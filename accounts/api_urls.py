from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .api import LoginApiView, LogoutApiView, MeApiView, RegisterApiView, UserViewSet

router = DefaultRouter()
router.register("users", UserViewSet, basename="user")

urlpatterns = [
    path("", include(router.urls)),
    path("register/", RegisterApiView.as_view(), name="ApiRegister"),
    path("login/", LoginApiView.as_view(), name="ApiLogin"),
    path("logout/", LogoutApiView.as_view(), name="ApiLogout"),
    path("me/", MeApiView.as_view(), name="ApiMe"),
]
