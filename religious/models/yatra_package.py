from django.db import models


class YatraPackage(models.Model):
    """
        Main master record for a pilgrimage / helicopter package.
    """

    class PackageType(models.TextChoices):
        CHAR_DHAM = "CHAR_DHAM", "Char Dham"
        DO_DHAM = "DO_DHAM", "Do Dham"

    package_code = models.CharField(
        max_length=50,
        unique=True,
        db_index=True,
    )

    slug = models.SlugField(
        max_length=150,
        unique=True,
        db_index=True,
    )
    
    package_type = models.CharField(
        max_length=30,
        choices=PackageType.choices,
    )

    title = models.CharField(max_length=255)

    subtitle = models.CharField(
        max_length=255,
        blank=True,
        default="",
    )

    description = models.TextField()

    duration_nights = models.PositiveSmallIntegerField()

    duration_days = models.PositiveSmallIntegerField()

    departure_location = models.CharField(
        max_length=255,
        blank=True,
        default="",
    )

    route = models.CharField(
        max_length=500,
        blank=True,
        default="",
    )

    operator_name = models.CharField(
        max_length=255,
        blank=True,
        default="",
    )

    season_year = models.PositiveIntegerField(
        null=True,
        blank=True,
    )

    hero_image_url = models.URLField(
        max_length=1000,
        blank=True,
        default="",
    )

    is_featured = models.BooleanField(default=False)

    is_active = models.BooleanField(default=True)

    display_order = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'YatraPackage'
        ordering = ["display_order", "id"]

    def __str__(self):
        return self.title