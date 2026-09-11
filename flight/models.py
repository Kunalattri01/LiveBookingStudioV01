from django.db import models

class Airport(models.Model):
    """
        Local airport/city master data used for homepage search UI
        (From/To autocomplete).

        This data belongs to our application, not to any flight supplier.
        It can be updated/imported independently (admin, management command,
        fixtures, future import job) regardless of which supplier(s) are
        used for actual flight inventory.
    """

    code = models.CharField(max_length=10, unique=True, db_index=True, help_text="3-letter IATA airport code, e.g. DEL", db_column="IATA_CODE")
    city = models.CharField(max_length=100, db_index=True, db_column="CITY")
    airport_name = models.CharField(max_length=255, db_column="AIRPORT_NAME")
    country = models.CharField(max_length=100, blank=True, default="India", db_column="COUNTRY")
    country_code = models.CharField(max_length=2, blank=True, default="IN", db_column="COUNTRY_CODE")
    is_popular = models.BooleanField(default=False, help_text="Shown first in the default/empty-query autocomplete list.", db_column="IS_POPULAR")
    is_active = models.BooleanField(default=True, help_text="Inactive airports are hidden from search without deleting them.", db_column="IS_ACTIVE")
    created_at = models.DateTimeField(auto_now_add=True, db_column="CREATED_AT")
    updated_at = models.DateTimeField(auto_now=True, db_column="UPDATED_AT")

    class Meta:
        db_table = 'Airport'
        ordering = ["city", "code"]
        indexes = [
            models.Index(fields=["is_active", "is_popular"]),
        ]

    def __str__(self):
        return f"{self.code} - {self.city}"

    def to_dict(self):
        """
            Shape matches what the existing homepage JS already expects
            (code / city / airport) so the frontend contract stays stable.
        """
        return {
            "code": self.code,
            "city": self.city,
            "airport": self.airport_name,
        }
