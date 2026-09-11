from django.urls import path

from .views import LoginView, LogoutView, ProfileView, RegisterView

urlpatterns = [
    path("login/", LoginView.as_view(), name="LoginPage"),
    path("register/", RegisterView.as_view(), name="RegisterPage"),
    path("logout/", LogoutView.as_view(), name="LogoutPage"),
    path("profile/", ProfileView.as_view(), name="ProfilePage"),
]
