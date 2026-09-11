from django.db import migrations

# Confirmed against a real, live TripJack sandbox Listing/Pricing/Review
# call (2026-09-11 / 2026-09-12, 1 adult): returns real room options,
# pricing and a bookable reviewHash/bookingId. Unlike the placeholder ID
# from the API reference doc, this one actually has inventory.
VERIFIED_LIVE_HOTEL = {
    "tj_hotel_id": "100000078396",
    "name": "Priya Living Flower Valley",
    "city": "Gurugram",
    "country": "India",
    "is_popular": True,
    "is_active": True,
}

# The API reference's sample ID returns totalResults: 0 for every date
# range tried against this account - it has no live inventory. Deactivate
# it rather than delete it, since it's still a documented example.
DEAD_PLACEHOLDER_ID = "10000000012345"


def seed_verified_hotel(apps, schema_editor):
    Hotel = apps.get_model("hotel", "Hotel")
    Hotel.objects.update_or_create(
        tj_hotel_id=VERIFIED_LIVE_HOTEL["tj_hotel_id"], defaults=VERIFIED_LIVE_HOTEL
    )
    Hotel.objects.filter(tj_hotel_id=DEAD_PLACEHOLDER_ID).update(is_active=False)


def reverse(apps, schema_editor):
    Hotel = apps.get_model("hotel", "Hotel")
    Hotel.objects.filter(tj_hotel_id=VERIFIED_LIVE_HOTEL["tj_hotel_id"]).delete()
    Hotel.objects.filter(tj_hotel_id=DEAD_PLACEHOLDER_ID).update(is_active=True)


class Migration(migrations.Migration):
    dependencies = [("hotel", "0002_seed_hotels")]

    operations = [migrations.RunPython(seed_verified_hotel, reverse)]
