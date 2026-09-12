from django.db import models
from religious.models import YatraPackage

class PackageGuideline(models.Model):
    """
    Important information and operational guidelines
    displayed on the package page.
    """

    package = models.ForeignKey(
        YatraPackage,
        on_delete=models.CASCADE,
        related_name="guidelines",
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
        db_table = 'PackageGuideline'
        ordering = ["display_order", "id"]