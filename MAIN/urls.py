"""
URL configuration for MAIN project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView, TemplateView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('robots.txt', TemplateView.as_view(template_name='robots.txt', content_type='text/plain')),
    path('', include('UserInterface.urls')),
    path('flight/', include('flight.urls')),
    path('api/v1/', include('flight.api.urls')),
    path('api/v1/', include('hotel.api.urls')),
    path('wishlist/', include('wishlist.urls')),
    path('hotel/', include('hotel.urls')),
    # The shared nav/footer templates link to /hotels (plural); the
    # actual hotel app is mounted at /hotel/ (singular). Redirect
    # rather than rename the route, to avoid touching those shared
    # templates for a hotel-app-scoped change.
    path('hotels', RedirectView.as_view(pattern_name='HotelPage', permanent=False)),
    path('hotels/', RedirectView.as_view(pattern_name='HotelPage', permanent=False)),
    path('support/', include('support.urls')),
    path('accounts/', include('accounts.urls')),
    path('legal/', include('legal.urls')),
    path('core/', include('core.urls')),
    path('api/v1/accounts/', include('accounts.api_urls')),
    path('api/v1/wishlist/', include('wishlist.api_urls')),
    path('api/v1/booking/', include('booking.urls')),
    path('api/v1/core/', include('core.urls')),
]
