from django.urls import path
from .views import YatraPackageDetailView

urlpatterns = [
    path('<slug:slug>/', YatraPackageDetailView.as_view(), name='YatraPackageDetailPage'),
]