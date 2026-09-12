from django.db import models
from religious.models import YatraPackage

class PackageItineraryDay(models.Model):
    """
    Day-wise itinerary for a package.
    """

    package = models.ForeignKey(
        YatraPackage,
        on_delete=models.CASCADE,
        related_name="itinerary_days",
    )

    day_number = models.PositiveSmallIntegerField()

    title = models.CharField(max_length=255)

    route = models.CharField(
        max_length=500,
        blank=True,
        default="",
    )

    overview = models.TextField()

    activities = models.JSONField(
        default=list,
        blank=True,
    )

    accommodation = models.CharField(
        max_length=255,
        blank=True,
        default="",
    )

    meal_information = models.CharField(
        max_length=500,
        blank=True,
        default="",
    )

    display_order = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = 'PackageItineraryDay'
        ordering = ["day_number"]
        constraints = [
            models.UniqueConstraint(
                fields=["package", "day_number"],
                name="unique_package_itinerary_day",
            )
        ]

    def __str__(self):
        return f"{self.package.title} - Day {self.day_number}"