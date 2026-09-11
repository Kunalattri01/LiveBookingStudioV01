import secrets

from .models import Booking


def make_booking_reference(prefix="TRV"):
    while True:
        reference = f"{prefix}-{secrets.token_hex(4).upper()}"
        if not Booking.objects.filter(reference=reference).exists():
            return reference
