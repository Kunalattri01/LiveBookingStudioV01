from django.urls import path
from .views import *

urlpatterns = [
    path('connect/', SupportView.as_view(), name="SupportPage"),
]