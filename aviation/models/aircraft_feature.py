from django.db import models
from aviation.models import Aircraft

class AircraftFeature(models.Model):
    """
        Stores aircraft features and amenities.

        Examples:
        - Luxury Leather Seats
        - Air Conditioning
        - Wi-Fi
        - Entertainment System
        - Spacious Cabin
        - Onboard Lavatory
    """

    id = models.AutoField(primary_key=True)
    aircraft = models.ForeignKey(Aircraft, on_delete=models.CASCADE,related_name="features")
    title = models.CharField(max_length=150)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=100, blank=True,help_text="Optional icon name or CSS class.")
    display_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'AircraftFeature'
        verbose_name = "Aircraft Feature"
        verbose_name_plural = "Aircraft Features"
        ordering = ["display_order", "id"]

    def __str__(self):
        return f"{self.aircraft.name} - {self.title}"