from django.db import models
from religious.models import YatraPackage

class PackageExclusion(models.Model):
    """
    Services / expenses not included in the package.
    """

    package = models.ForeignKey(
        YatraPackage,
        on_delete=models.CASCADE,
        related_name="exclusions",
    )

    title = models.CharField(max_length=255)

    description = models.TextField()

    display_order = models.PositiveIntegerField(default=0)

    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'PackageExclusion'
        ordering = ["display_order", "id"]