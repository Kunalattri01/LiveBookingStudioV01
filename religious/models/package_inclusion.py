from django.db import models
from religious.models import YatraPackage

class PackageInclusion(models.Model):
    """
    Services included in the package.
    """

    package = models.ForeignKey(
        YatraPackage,
        on_delete=models.CASCADE,
        related_name="inclusions",
    )

    title = models.CharField(max_length=255)

    description = models.TextField()

    display_order = models.PositiveIntegerField(default=0)

    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'PackageInclusion'
        ordering = ["display_order", "id"]