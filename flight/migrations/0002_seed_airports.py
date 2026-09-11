from django.db import migrations

AIRPORTS = [
    {"code": "DEL", "city": "New Delhi", "airport_name": "Indira Gandhi International Airport", "country": "India", "country_code": "IN", "is_popular": True},
    {"code": "BOM", "city": "Mumbai", "airport_name": "Chhatrapati Shivaji Maharaj International Airport", "country": "India", "country_code": "IN", "is_popular": True},
    {"code": "BLR", "city": "Bengaluru", "airport_name": "Kempegowda International Airport", "country": "India", "country_code": "IN", "is_popular": True},
    {"code": "HYD", "city": "Hyderabad", "airport_name": "Rajiv Gandhi International Airport", "country": "India", "country_code": "IN", "is_popular": True},
    {"code": "MAA", "city": "Chennai", "airport_name": "Chennai International Airport", "country": "India", "country_code": "IN", "is_popular": True},
    {"code": "CCU", "city": "Kolkata", "airport_name": "Netaji Subhas Chandra Bose International Airport", "country": "India", "country_code": "IN", "is_popular": False},
    {"code": "GOI", "city": "Goa", "airport_name": "Manohar International Airport", "country": "India", "country_code": "IN", "is_popular": True},
    {"code": "AMD", "city": "Ahmedabad", "airport_name": "Sardar Vallabhbhai Patel International Airport", "country": "India", "country_code": "IN", "is_popular": False},
    {"code": "PNQ", "city": "Pune", "airport_name": "Pune International Airport", "country": "India", "country_code": "IN", "is_popular": False},
    {"code": "COK", "city": "Kochi", "airport_name": "Cochin International Airport", "country": "India", "country_code": "IN", "is_popular": False},
    {"code": "DXB", "city": "Dubai", "airport_name": "Dubai International Airport", "country": "United Arab Emirates", "country_code": "AE", "is_popular": True},
    {"code": "JFK", "city": "New York", "airport_name": "John F. Kennedy International Airport", "country": "United States", "country_code": "US", "is_popular": False},
    {"code": "SIN", "city": "Singapore", "airport_name": "Singapore Changi Airport", "country": "Singapore", "country_code": "SG", "is_popular": False},
    {"code": "LHR", "city": "London", "airport_name": "Heathrow Airport", "country": "United Kingdom", "country_code": "GB", "is_popular": False},
    {"code": "DOH", "city": "Doha", "airport_name": "Hamad International Airport", "country": "Qatar", "country_code": "QA", "is_popular": False},
]


def seed_airports(apps, schema_editor):
    Airport = apps.get_model("flight", "Airport")
    for entry in AIRPORTS:
        Airport.objects.update_or_create(
            code=entry["code"],
            defaults={
                "city": entry["city"],
                "airport_name": entry["airport_name"],
                "country": entry["country"],
                "country_code": entry["country_code"],
                "is_popular": entry["is_popular"],
                "is_active": True,
            },
        )


def remove_seeded_airports(apps, schema_editor):
    Airport = apps.get_model("flight", "Airport")
    codes = [entry["code"] for entry in AIRPORTS]
    Airport.objects.filter(code__in=codes).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("flight", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(seed_airports, remove_seeded_airports),
    ]
