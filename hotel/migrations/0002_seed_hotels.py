from django.db import migrations

# Only this tj_hotel_id is verified against the TripJack Hotel API v3
# reference (used throughout its sample requests/responses). Add real
# TripJack hotel IDs here as they become available - see the note in
# hotel/models.py.
SEED_HOTELS = [
    {
        "tj_hotel_id": "10000000012345",
        "name": "Pride Plaza Hotel Aerocity New Delhi",
        "city": "Delhi",
        "country": "India",
        "is_popular": True,
    },
]


def seed_hotels(apps, schema_editor):
    Hotel = apps.get_model("hotel", "Hotel")
    for entry in SEED_HOTELS:
        Hotel.objects.update_or_create(tj_hotel_id=entry["tj_hotel_id"], defaults=entry)


def remove_seeded_hotels(apps, schema_editor):
    Hotel = apps.get_model("hotel", "Hotel")
    Hotel.objects.filter(tj_hotel_id__in=[entry["tj_hotel_id"] for entry in SEED_HOTELS]).delete()


class Migration(migrations.Migration):
    dependencies = [("hotel", "0001_initial")]

    operations = [migrations.RunPython(seed_hotels, remove_seeded_hotels)]
