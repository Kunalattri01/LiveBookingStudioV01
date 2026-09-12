from django.db import models
from django.core.validators import MinValueValidator
from aviation.models import Aircraft

class AircraftService(models.Model):
    """
        Optional services related to a particular aircraft.

        Examples:
        - Catering
        - Airport Transfer
        - Ground Handling
        - Additional Baggage
        - VIP Assistance
    """

    id = models.AutoField(primary_key=True)
    aircraft = models.ForeignKey(Aircraft, on_delete=models.CASCADE, related_name="services")
    name = models.CharField(max_length=150)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True, validators=[MinValueValidator(0)])
    currency = models.CharField(max_length=3, default="INR")
    price_unit = models.CharField(max_length=50, blank=True)
    is_price_on_request = models.BooleanField(default=True)
    display_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'AircraftService'
        verbose_name = "Aircraft Service"
        verbose_name_plural = "Aircraft Services"
        ordering = ["display_order", "name"]

    def __str__(self):
        return f"{self.aircraft.name} - {self.name}"