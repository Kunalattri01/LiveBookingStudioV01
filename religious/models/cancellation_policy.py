from django.db import models
from religious.models import YatraPackage

class PackageCancellationPolicy(models.Model):
    """
    General cancellation and refund policy.
    """

    package = models.OneToOneField(
        YatraPackage,
        on_delete=models.CASCADE,
        related_name="cancellation_policy",
    )

    cancellation_description = models.TextField()

    refund_description = models.TextField()

    cancellation_must_be_in_writing = models.BooleanField(
        default=False,
    )

    refund_processing_days_min = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
    )

    refund_processing_days_max = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
    )

    weather_refund_description = models.TextField(
        blank=True,
        default="",
    )

    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'PackageCancellationPolicy'


class PackageCancellationRule(models.Model):
    """
    Individual cancellation slabs.
    """

    policy = models.ForeignKey(
        PackageCancellationPolicy,
        on_delete=models.CASCADE,
        related_name="rules",
    )

    minimum_days_before = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
    )

    maximum_days_before = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
    )

    cancellation_charge_percent = models.DecimalField(
        max_digits=5,
        decimal_places=2,
    )

    refund_percent = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
    )

    description = models.TextField(
        blank=True,
        default="",
    )

    display_order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        db_table = 'PackageCancellationRule'
        ordering = ["display_order", "id"]