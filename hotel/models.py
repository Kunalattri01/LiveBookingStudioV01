from django.db import models


class Hotel(models.Model):
    """
    Local master data mapping a destination to TripJack hotel IDs.

    TripJack Hotel API v3 removed `cityCode` from the Listing request -
    it only accepts `hids` (specific TripJack hotel IDs), so a
    free-text destination search has nowhere to resolve to on
    TripJack's side. This table is our own catalog of tjHotelId values
    per city, used to turn "Delhi" into the `hids` array the Listing
    API actually accepts - the same role `flight.models.Airport` plays
    for resolving a typed city/airport name to an IATA code.

    tj_hotel_id="100000078396" (Priya Living Flower Valley, Gurugram) is
    confirmed against a real, live TripJack sandbox Listing/Pricing/
    Review call - see hotel/migrations/0003_seed_verified_hotel.py.
    tj_hotel_id="10000000012345" (the API reference doc's sample ID) is
    seeded but marked inactive: it consistently returns zero results
    for every date range tried against this account, so it has no
    live inventory.

    Bulk-populated for real by `python manage.py seed_tripjack_hotels`
    (see hotel/management/commands/seed_tripjack_hotels.py), which
    pulls real hotel IDs/names/images from TripJack's
    fetch-hotel-mapping / fetch-hotel-content static-content endpoints
    - undocumented in the v3 partner reference, confirmed by direct
    live probing (see hotel/providers/tripjack_client.py).

    image_url is a hero image straight from TripJack's own static
    content (fetch-hotel-content), not fabricated - stored locally
    because TripJack's Listing/Pricing responses never include images,
    only the separate static-content endpoints do.
    """

    tj_hotel_id = models.CharField(max_length=32, unique=True, db_index=True)
    name = models.CharField(max_length=255)
    city = models.CharField(max_length=120, db_index=True)
    country = models.CharField(max_length=120, blank=True, default="India")
    image_url = models.URLField(max_length=500, blank=True, default="")
    star_rating = models.PositiveSmallIntegerField(null=True, blank=True)
    is_popular = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["city", "name"]
        indexes = [models.Index(fields=["is_active", "is_popular"])]

    def __str__(self):
        return f"{self.name} ({self.city})"

    def to_dict(self):
        return {
            "tj_hotel_id": self.tj_hotel_id,
            "name": self.name,
            "city": self.city,
            "image_url": self.image_url,
            "star_rating": self.star_rating,
        }
