from django.db import models
from religious.models import YatraPackage

class PackageHotel(models.Model):
    """
    Hotel / resort assigned to a destination in the itinerary.
    """

    package = models.ForeignKey(
        YatraPackage,
        on_delete=models.CASCADE,
        related_name="hotels",
    )

    destination = models.CharField(
        max_length=150,
    )

    location = models.CharField(
        max_length=255,
        blank=True,
        default="",
    )

    hotel_name = models.CharField(
        max_length=255,
    )

    hotel_type = models.CharField(
        max_length=100,
        blank=True,
        default="",
    )

    description = models.TextField(
        blank=True,
        default="",
    )

    alternative_text = models.CharField(
        max_length=255,
        blank=True,
        default="",
    )

    image_url = models.URLField(
        max_length=1000,
        blank=True,
        default="",
    )

    display_order = models.PositiveIntegerField(default=0)

    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'PackageHotel'
        ordering = ["display_order", "id"]