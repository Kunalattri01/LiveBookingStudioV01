from django.db import models
from religious.models import YatraPackage


class PackageBaggagePolicy(models.Model):
    """
    Passenger weight and baggage rules.
    """

    package = models.OneToOneField(
        YatraPackage,
        on_delete=models.CASCADE,
        related_name="baggage_policy",
    )

    max_standard_weight_kg = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True,
    )

    overweight_charge_per_kg = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
    )

    luggage_limit_kg = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True,
    )

    weight_declaration_required = models.BooleanField(
        default=False,
    )

    weight_verification_required = models.BooleanField(
        default=False,
    )

    soft_bags_only = models.BooleanField(
        default=False,
    )

    excess_baggage_storage_available = models.BooleanField(
        default=False,
    )

    description = models.TextField(
        blank=True,
        default="",
    )

    is_active = models.BooleanField(default=True)


    class Meta:
        db_table = 'PackageBaggagePolicy'