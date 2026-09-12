from django.db import models
from religious.models import YatraPackage

class PackagePricing(models.Model):
    """
    Pricing options for a package.
    """

    package = models.ForeignKey(
        YatraPackage,
        on_delete=models.CASCADE,
        related_name="pricing_options",
    )

    plan_name = models.CharField(
        max_length=100,
    )

    price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
    )

    price_label = models.CharField(
        max_length=100,
        blank=True,
        default="",
    )

    currency = models.CharField(
        max_length=10,
        default="INR",
    )

    pricing_unit = models.CharField(
        max_length=100,
        default="per person",
    )

    description = models.TextField(
        blank=True,
        default="",
    )

    is_custom_price = models.BooleanField(
        default=False,
    )

    display_order = models.PositiveIntegerField(default=0)

    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'PackagePricing'
        ordering = ["display_order", "id"]

    def __str__(self):
        return f"{self.package.title} - {self.plan_name}"