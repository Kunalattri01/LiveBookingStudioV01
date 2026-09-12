from django.db import models
from django.urls import reverse

class AircraftCategory(models.Model):
    """
        Stores aircraft categories such as:
        - Helicopters
        - Private Jets
        - Business Jets
        - Commercial Aircraft
        - Turboprops
    """

    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=120, unique=True)
    short_description = models.CharField(max_length=255, blank=True)
    description = models.TextField(blank=True)
    image_url = models.URLField(blank=True, help_text="Category image URL.")
    display_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'AircraftCategory'
        verbose_name = "Aircraft Category"
        verbose_name_plural = "Aircraft Categories"
        ordering = ["display_order", "name"]

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse(
            "aviation:aircraft-list",
            kwargs={"slug": self.slug}
        )