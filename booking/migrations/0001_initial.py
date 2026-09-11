import uuid
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


def booking_uuid():
    return uuid.uuid4()


class Migration(migrations.Migration):
    initial = True
    dependencies = [migrations.swappable_dependency(settings.AUTH_USER_MODEL)]
    operations = [
        migrations.CreateModel(
            name="Booking",
            fields=[
                ("id", models.UUIDField(default=booking_uuid, editable=False, primary_key=True, serialize=False)),
                ("reference", models.CharField(db_index=True, max_length=24, unique=True)),
                ("booking_type", models.CharField(choices=[("flight", "Flight"), ("hotel", "Hotel"), ("cab", "Cab"), ("other", "Other")], max_length=20)),
                ("status", models.CharField(choices=[("draft", "Draft"), ("pending", "Pending"), ("confirmed", "Confirmed"), ("cancelled", "Cancelled"), ("failed", "Failed"), ("completed", "Completed")], db_index=True, default="draft", max_length=20)),
                ("supplier_name", models.CharField(blank=True, max_length=80)),
                ("supplier_reference", models.CharField(blank=True, max_length=120)),
                ("total_amount", models.DecimalField(decimal_places=2, default=0, max_digits=12)),
                ("currency", models.CharField(default="INR", max_length=3)),
                ("search_reference", models.CharField(blank=True, max_length=120)),
                ("contact_name", models.CharField(blank=True, max_length=160)),
                ("contact_email", models.EmailField(blank=True, max_length=254)),
                ("contact_phone", models.CharField(blank=True, max_length=30)),
                ("metadata", models.JSONField(blank=True, default=dict)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="bookings", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ["-created_at"]},
        ),
        migrations.CreateModel(
            name="BookingItem",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("item_type", models.CharField(max_length=30)),
                ("name", models.CharField(max_length=255)),
                ("description", models.TextField(blank=True)),
                ("quantity", models.PositiveIntegerField(default=1)),
                ("unit_price", models.DecimalField(decimal_places=2, default=0, max_digits=12)),
                ("metadata", models.JSONField(blank=True, default=dict)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("booking", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="items", to="booking.booking")),
            ],
            options={"ordering": ["id"]},
        ),
        migrations.CreateModel(
            name="PaymentTransaction",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("transaction_id", models.CharField(max_length=120, unique=True)),
                ("provider", models.CharField(blank=True, max_length=80)),
                ("payment_method", models.CharField(blank=True, max_length=50)),
                ("status", models.CharField(choices=[("initiated", "Initiated"), ("pending", "Pending"), ("success", "Success"), ("failed", "Failed"), ("refunded", "Refunded")], default="initiated", max_length=20)),
                ("amount", models.DecimalField(decimal_places=2, max_digits=12)),
                ("currency", models.CharField(default="INR", max_length=3)),
                ("provider_reference", models.CharField(blank=True, max_length=120)),
                ("failure_reason", models.TextField(blank=True)),
                ("metadata", models.JSONField(blank=True, default=dict)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("booking", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="payments", to="booking.booking")),
            ],
            options={"ordering": ["-created_at"]},
        ),
    ]
