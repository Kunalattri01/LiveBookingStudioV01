from django.db import models
from religious.models import YatraPackage

class PackageImage(models.Model):
    
    class ImageType(models.TextChoices):
        HERO = "HERO", "Hero"
        EXPERIENCE = "EXPERIENCE", "Experience"
        ITINERARY = "ITINERARY", "Itinerary"
        DESTINATION = "DESTINATION", "Destination"
        HOTEL = "HOTEL", "Hotel"
        GALLERY = "GALLERY", "Gallery"

    package = models.ForeignKey(
        YatraPackage,
        on_delete=models.CASCADE,
        related_name="images",
    )

    image_type = models.CharField(
        max_length=30,
        choices=ImageType.choices,
        default=ImageType.GALLERY,
    )

    image_url = models.URLField(
        max_length=1000,
    )

    title = models.CharField(
        max_length=255,
        blank=True,
        default="",
    )

    alt_text = models.CharField(
        max_length=255,
        blank=True,
        default="",
    )

    caption = models.CharField(
        max_length=500,
        blank=True,
        default="",
    )

    display_order = models.PositiveIntegerField(
        default=0,
    )

    is_active = models.BooleanField(
        default=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        db_table = "PackageImage"
        ordering = ["display_order", "id"]
        indexes = [
            models.Index(
                fields=["package", "image_type", "is_active"]
            ),
        ]

    def __str__(self):
        return self.title or f"{self.package.title} Image"