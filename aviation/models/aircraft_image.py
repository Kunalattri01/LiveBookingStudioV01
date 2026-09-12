from django.db import models
from aviation.models import Aircraft

class AircraftImage(models.Model):
    """
        Stores all images associated with an aircraft.
    """

    class ImageType(models.TextChoices):
        HERO = "HERO", "Hero Image"
        EXTERIOR = "EXTERIOR", "Exterior"
        INTERIOR = "INTERIOR", "Interior"
        CABIN = "CABIN", "Cabin"
        COCKPIT = "COCKPIT", "Cockpit"
        SEAT_MAP = "SEAT_MAP", "Seat Map"
        GALLERY = "GALLERY", "Gallery"
        OTHER = "OTHER", "Other"

    id = models.AutoField(primary_key=True)
    aircraft = models.ForeignKey(Aircraft,on_delete=models.CASCADE,related_name="images")
    image_type = models.CharField(max_length=20,choices=ImageType.choices,default=ImageType.GALLERY)
    image_url = models.URLField()
    title = models.CharField(max_length=150,blank=True)
    alt_text = models.CharField(max_length=255,blank=True)
    caption = models.CharField(max_length=255,blank=True)
    display_order = models.PositiveIntegerField(default=0)
    is_primary = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:

        db_table = "AircraftImage"
        verbose_name = "Aircraft Image"
        verbose_name_plural = "Aircraft Images"
        ordering = ["display_order", "id"]
        indexes = [
            models.Index(
                fields=["aircraft", "image_type"]
            ),
            models.Index(
                fields=["aircraft", "is_active"]
            ),
        ]

    def __str__(self):
        return f"{self.aircraft.name} - {self.image_type}"