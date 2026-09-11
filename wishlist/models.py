from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models


class Wishlist(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="wishlists")
    name = models.CharField(max_length=120, default="My Wishlist")
    is_default = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["user", "name"], name="unique_wishlist_per_user")]
        ordering = ["name"]

    def __str__(self):
        return f"{self.user} - {self.name}"


class WishlistItem(models.Model):
    wishlist = models.ForeignKey(Wishlist, on_delete=models.CASCADE, related_name="items")
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.CharField(max_length=120)
    content_object = GenericForeignKey("content_type", "object_id")
    title = models.CharField(max_length=255)
    subtitle = models.CharField(max_length=255, blank=True)
    image_url = models.URLField(blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["wishlist", "content_type", "object_id"],
                name="unique_wishlist_item",
            )
        ]
        ordering = ["-created_at"]
