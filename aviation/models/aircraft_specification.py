from django.db import models
from aviation.models import Aircraft


class AircraftSpecification(models.Model):
    """
        Stores flexible technical specifications.

        Examples:
        - Maximum Takeoff Weight: 3,175 kg
        - Engine Type: Pratt & Whitney
        - Engine Count: 2
        - Cabin Length: 6.2 m
        - Cabin Width: 1.8 m
        - Maximum Altitude: 41,000 ft
    """

    id = models.AutoField(primary_key=True)
    aircraft = models.ForeignKey(Aircraft, on_delete=models.CASCADE, related_name="specifications")
    section_name = models.CharField(max_length=100, default="Technical Specifications")
    group_name = models.CharField(max_length=100, blank=True)
    label = models.CharField(max_length=150)
    value = models.CharField(max_length=255)
    unit = models.CharField(max_length=50, blank=True)
    display_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:

        db_table = 'AircraftSpecification'
        verbose_name = "Aircraft Specification"
        verbose_name_plural = "Aircraft Specifications"
        ordering = [ "section_name", "group_name", "display_order", "id" ]
        indexes = [
            models.Index(
                fields=["aircraft", "section_name"]
            ),
            models.Index(
                fields=["aircraft", "is_active"]
            ),
        ]

    def __str__(self):
        return f"{self.aircraft.name} - {self.label}"