from django.db import models
from religious.models import YatraPackage

class PackageSafetyGuideline(models.Model):
    """
    Passenger conduct and safety information.
    """

    package = models.ForeignKey(
        YatraPackage,
        on_delete=models.CASCADE,
        related_name="safety_guidelines",
    )

    category = models.CharField(
        max_length=100,
    )

    title = models.CharField(
        max_length=255,
    )

    description = models.TextField()

    display_order = models.PositiveIntegerField(default=0)

    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'PackageSafetyGuideline'
        ordering = ["display_order", "id"]