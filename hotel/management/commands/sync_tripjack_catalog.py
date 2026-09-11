"""
Single entry point for scheduled, automatic refreshes of the local
Hotel catalog from live TripJack data.

This exists so the catalog doesn't stay a one-off manual snapshot: an
external scheduler (OS cron, a systemd timer, or a hosting platform's
scheduled-task feature - whichever this project is actually deployed
with) can call this one command on a timer, and it re-runs the already
verified seed_tripjack_hotels presets against the live TripJack
fetch-hotel-mapping / fetch-hotel-content endpoints.

Why this, and not a "sync" API call: TripJack's v3 partner reference
documents a Hotel Mapping *Sync* and a Deleted Mapping Sync endpoint
(see hotel/providers/tripjack_client.py), but their request/response
shape has never been seen or verified in this codebase - only
fetch-hotel-mapping and fetch-hotel-content were confirmed by direct
live probing. Rather than guess a path/payload for the Sync endpoints,
this command re-runs the same verified full-mapping pull on a timer.
`Hotel.objects.update_or_create` (in seed_tripjack_hotels.py) makes
that idempotent and safe to repeat.

KNOWN LIMITATION: because there's no verified Deleted Mapping Sync
call, this command only adds/updates hotels - it never deactivates a
row whose tjHotelId TripJack has delisted. A hotel that vanishes from
TripJack's live mapping will stay in the local catalog (and can still
be searched) until someone confirms and implements that endpoint.

Usage (manual):
    python manage.py sync_tripjack_catalog

Usage (cron, daily at 03:00, from a checked-out copy at /srv/app with
a virtualenv at /srv/app/.venv):
    0 3 * * * cd /srv/app && /srv/app/.venv/bin/python manage.py sync_tripjack_catalog >> /var/log/tripjack_sync.log 2>&1
"""

from django.conf import settings
from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone


class Command(BaseCommand):
    help = "Re-run the seed_tripjack_hotels presets on a schedule to keep the local Hotel catalog fresh."

    def add_arguments(self, parser):
        parser.add_argument(
            "--limit",
            type=int,
            default=100,
            help="Max hotels to pull per city/country, passed through to seed_tripjack_hotels. Default 100.",
        )
        parser.add_argument(
            "--presets",
            nargs="+",
            default=["major-india", "global-countries"],
            choices=["major-india", "global-countries"],
            help="Which seed_tripjack_hotels presets to refresh. Default: both.",
        )

    def handle(self, *args, **options):
        provider = (getattr(settings, "HOTEL_PROVIDER", "") or "").strip().lower()
        if provider != "tripjack":
            raise CommandError(
                "HOTEL_PROVIDER must be 'tripjack' to sync from live TripJack data "
                f"(currently '{provider or 'unset'}')."
            )

        limit = options["limit"]
        presets = options["presets"]
        started = timezone.now()
        self.stdout.write(f"[{started.isoformat()}] Starting TripJack catalog sync ({', '.join(presets)})...")

        for preset in presets:
            self.stdout.write(f"-- preset: {preset} --")
            call_command("seed_tripjack_hotels", preset=preset, limit=limit)

        finished = timezone.now()
        self.stdout.write(
            self.style.SUCCESS(
                f"[{finished.isoformat()}] TripJack catalog sync finished in {(finished - started).total_seconds():.1f}s."
            )
        )
