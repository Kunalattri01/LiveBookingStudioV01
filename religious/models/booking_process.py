from django.db import models
from religious.models import YatraPackage
    
class PackageBookingStep(models.Model):
    """
    Step-by-step booking process.
    """

    package = models.ForeignKey(
        YatraPackage,
        on_delete=models.CASCADE,
        related_name="booking_steps",
    )

    step_number = models.PositiveSmallIntegerField()

    title = models.CharField(
        max_length=255,
    )

    description = models.TextField()

    display_order = models.PositiveSmallIntegerField(default=0)

    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'PackageBookingStep'
        ordering = ["step_number"]
        constraints = [
            models.UniqueConstraint(
                fields=["package", "step_number"],
                name="unique_package_booking_step",
            )
        ]