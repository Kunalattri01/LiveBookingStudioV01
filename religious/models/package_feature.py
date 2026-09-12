from django.db import models
from religious.models import YatraPackage

class PackageFeature(models.Model):
    """
    Features / experience highlights displayed on the package page.
    """

    package = models.ForeignKey(
        YatraPackage,
        on_delete=models.CASCADE,
        related_name="features",
    )

    title = models.CharField(max_length=255)

    description = models.TextField()

    icon = models.CharField(
        max_length=100,
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
        db_table = 'PackageFeature'
        ordering = ["display_order", "id"]

    def __str__(self):
        return self.title