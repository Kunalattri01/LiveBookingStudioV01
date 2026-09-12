from django.db import models
from django.urls import reverse
from django.core.validators import MinValueValidator

from aviation.models import AircraftCategory

class Aircraft(models.Model):
    """
        Stores the main aircraft information used by:
        - Aircraft listing cards
        - Aircraft detail pages
        - Search and filtering
    """

    class AircraftType(models.TextChoices):
        HELICOPTER = "HELICOPTER", "Helicopter"
        PRIVATE_JET = "PRIVATE_JET", "Private Jet"
        BUSINESS_JET = "BUSINESS_JET", "Business Jet"
        COMMERCIAL = "COMMERCIAL", "Commercial Aircraft"
        TURBOPROP = "TURBOPROP", "Turboprop"
        OTHER = "OTHER", "Other"

    class SpeedUnit(models.TextChoices):
        KNOTS = "knots", "Knots"
        KMH = "km/h", "Kilometers per hour"
        MPH = "mph", "Miles per hour"

    class DistanceUnit(models.TextChoices):
        KM = "km", "Kilometers"
        MILES = "miles", "Miles"
        NM = "nm", "Nautical miles"

    class LuggageUnit(models.TextChoices):
        KG = "kg", "Kilograms"
        LB = "lb", "Pounds"
        LITERS = "liters", "Liters"

    class PriceUnit(models.TextChoices):
        HOUR = "hour", "Per Hour"
        DAY = "day", "Per Day"
        TRIP = "trip", "Per Trip"
        FLIGHT = "flight", "Per Flight"
        REQUEST = "request", "On Request"

    category = models.ForeignKey(AircraftCategory, on_delete=models.PROTECT, related_name="aircraft")

    aircraft_type = models.CharField(max_length=30,choices=AircraftType.choices,default=AircraftType.OTHER)

    name = models.CharField(
        max_length=150
    )

    slug = models.SlugField(
        max_length=180,
        unique=True
    )

    manufacturer = models.CharField(
        max_length=100,
        blank=True
    )

    model_name = models.CharField(
        max_length=100,
        blank=True
    )

    short_description = models.CharField(
        max_length=500,
        blank=True
    )

    description = models.TextField(
        blank=True
    )

    primary_image_url = models.URLField(
        blank=True,
        help_text="Main image displayed on aircraft cards."
    )

    # ---------------------------------------------------------
    # Listing-card information
    # ---------------------------------------------------------

    passenger_capacity = models.PositiveIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1)],
        help_text="Maximum number of passengers."
    )

    cruising_speed = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )

    speed_unit = models.CharField(
        max_length=20,
        choices=SpeedUnit.choices,
        default=SpeedUnit.KNOTS
    )

    luggage_capacity = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )

    luggage_unit = models.CharField(
        max_length=20,
        choices=LuggageUnit.choices,
        default=LuggageUnit.KG
    )

    pilot_count = models.PositiveIntegerField(
        default=1
    )

    flight_attendant_count = models.PositiveIntegerField(
        default=0
    )

    has_flight_attendant = models.BooleanField(
        default=False
    )

    range_value = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True
    )

    range_unit = models.CharField(
        max_length=20,
        choices=DistanceUnit.choices,
        default=DistanceUnit.KM
    )

    # ---------------------------------------------------------
    # Detail-page cabin information
    # ---------------------------------------------------------

    lavatory_count = models.PositiveIntegerField(
        default=0
    )

    wifi_available = models.BooleanField(
        default=False
    )

    cabin_description = models.TextField(
        blank=True
    )

    # ---------------------------------------------------------
    # Pricing information
    # ---------------------------------------------------------

    starting_price = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)]
    )

    price_currency = models.CharField(
        max_length=3,
        default="INR"
    )

    price_unit = models.CharField(
        max_length=20,
        choices=PriceUnit.choices,
        default=PriceUnit.REQUEST
    )

    is_price_on_request = models.BooleanField(
        default=True
    )

    # ---------------------------------------------------------
    # Publishing and display controls
    # ---------------------------------------------------------

    is_featured = models.BooleanField(
        default=False
    )

    is_active = models.BooleanField(
        default=True
    )

    display_order = models.PositiveIntegerField(
        default=0
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:

        db_table = 'Aircraft'
        verbose_name = "Aircraft"
        verbose_name_plural = "Aircraft"
        ordering = ["display_order", "name"]
        indexes = [
            models.Index(
                fields=["category", "is_active"]
            ),
            models.Index(
                fields=["aircraft_type", "is_active"]
            ),
            models.Index(
                fields=["is_featured", "is_active"]
            ),
        ]

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse(
            "aviation:aircraft-detail",
            kwargs={"slug": self.slug}
        )

        