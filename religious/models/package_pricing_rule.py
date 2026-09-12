from django.db import models
from religious.models import YatraPackage

class PackagePricingRule(models.Model):
    """
    Additional pricing rules such as single occupancy,
    infant pricing, supplements, etc.
    """

    package = models.ForeignKey(
        YatraPackage,
        on_delete=models.CASCADE,
        related_name="pricing_rules",
    )

    title = models.CharField(max_length=255)

    description = models.TextField()

    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
    )

    currency = models.CharField(
        max_length=10,
        default="INR",
    )

    display_order = models.PositiveIntegerField(default=0)

    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'PackagePricingRule'
        ordering = ["display_order", "id"]