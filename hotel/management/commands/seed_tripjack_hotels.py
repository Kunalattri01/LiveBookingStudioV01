"""
Seeds the local Hotel catalog (hotel/models.py) with real TripJack
hotel IDs, pulled live from the fetch-hotel-mapping / fetch-hotel-content
static-content endpoints (see hotel/providers/tripjack_client.py for
how their shape was confirmed - not documented in the v3 partner
reference, discovered by direct probing).

This exists because TripJack's Listing API (v3) only accepts explicit
`hids` - there is no free-text/city search on the live booking-flow
endpoints. The local Hotel table is what turns a typed destination
into the `hids` array Listing actually accepts, and until now it held
exactly one hand-verified row.

Usage:
    python manage.py seed_tripjack_hotels --city "Gurugram" --citycode 682696 --limit 100
    python manage.py seed_tripjack_hotels --preset major-india --limit 100
    python manage.py seed_tripjack_hotels --country "France" --limit 200
    python manage.py seed_tripjack_hotels --preset global-countries --limit 200

`--preset major-india` seeds a curated set of major Indian cities using
citycodes discovered by sampling real TripJack hotel content live
(see docs/tripjack-integration.md for how these were found). Requires
HOTEL_PROVIDER=tripjack and a working, whitelisted TRIPJACK_API_KEY.

`--country "<name>"` / `--preset global-countries` seed by TripJack's
`countryName` filter on fetch-hotel-mapping instead of a citycode -
confirmed live (by the project owner, see hotel/providers/tripjack_client.py)
to filter the ~1.57M-hotel global catalog down to one country, unlike
`cityName`/`regionName` which the same probing found are silently
ignored. Fetching per-hotel `locale.address.citycode`-level granularity
for arbitrary world cities isn't possible here because their citycodes
have never been discovered (only India's have - see MAJOR_INDIA_CITIES
below), and this project's convention is to never guess an unverified
field/value. So country-scoped rows are stored with `city` set to the
country name itself (coarser than the citycode-level India rows) -
still enough to resolve a typed country into the `hids` array Listing
needs, just not city-granular for these entries.

`global-countries` is a curated ~60-country list spanning every
inhabited continent, not literally all ~195 countries recognised
worldwide - see GLOBAL_COUNTRIES below. A country name that doesn't
match TripJack's internal naming simply yields zero hotels and is
skipped with a warning, same as any other empty result.
"""

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from hotel.models import Hotel
from hotel.providers.tripjack_client import TripJackHotelClient
from hotel.providers.tripjack_exceptions import TripJackHotelError

# Citycodes discovered live on 2026-09-07 by sampling real India hotel
# content via fetch-hotel-content and reading locale.address.citycode -
# not from any documented TripJack endpoint. Re-verify if TripJack ever
# changes its region ID scheme.
MAJOR_INDIA_CITIES = {
    "NEW DELHI": 727635,
    "BENGALURU": 740075,
    "MUMBAI": 740051,
    "JAIPUR": 739239,
    "CHENNAI": 738801,
    "HYDERABAD": 739343,
    "UDAIPUR": 737646,
    "GURUGRAM": 682696,
    "KOLKATA": 739947,
    "JODHPUR": 739231,
    "PUNE": 707176,
    "AGRA": 740325,
    "GOA": 701645,  # PANAJI citycode - used as the Goa catalog entry point
}

# A broad, curated list of country names spanning every inhabited
# continent, used with fetch-hotel-mapping's confirmed-live `countryName`
# filter (see hotel/providers/tripjack_client.py) for the `global-countries`
# preset. Not exhaustive (~195 countries exist) and not verified name-by-
# name against TripJack's internal naming - a mismatch just returns zero
# hotels for that entry and is skipped, same as any other empty result.
GLOBAL_COUNTRIES = [
    # Asia
    "Thailand", "Singapore", "Malaysia", "Indonesia", "Japan", "South Korea",
    "China", "Vietnam", "Philippines", "Sri Lanka", "Nepal", "Maldives",
    "Cambodia", "Hong Kong", "Macau", "Taiwan",
    # Middle East
    "United Arab Emirates", "Saudi Arabia", "Qatar", "Turkey", "Israel",
    "Jordan", "Oman", "Bahrain", "Kuwait",
    # Europe
    "United Kingdom", "France", "Germany", "Italy", "Spain", "Portugal",
    "Netherlands", "Switzerland", "Austria", "Greece", "Ireland", "Belgium",
    "Sweden", "Norway", "Denmark", "Poland", "Czech Republic", "Hungary",
    "Russia", "Croatia", "Iceland", "Finland",
    # Americas
    "United States", "Canada", "Mexico", "Brazil", "Argentina", "Chile",
    "Peru", "Colombia", "Costa Rica", "Cuba",
    # Oceania
    "Australia", "New Zealand", "Fiji",
    # Africa
    "South Africa", "Egypt", "Morocco", "Kenya", "Mauritius", "Tanzania",
]


class Command(BaseCommand):
    help = "Seed the local Hotel catalog with real TripJack hotel IDs for one city or a preset city list."

    def add_arguments(self, parser):
        parser.add_argument("--city", type=str, help="City name to store on seeded rows (e.g. 'Gurugram').")
        parser.add_argument("--citycode", type=int, help="TripJack numeric region/city code (locale.address.citycode).")
        parser.add_argument(
            "--country",
            type=str,
            help="Country name to filter fetch-hotel-mapping by (TripJack's confirmed `countryName` filter), "
            "instead of a --city/--citycode pair. Seeded rows store this country name as `city` too, since "
            "per-hotel citycodes for arbitrary world cities aren't known (see module docstring).",
        )
        parser.add_argument(
            "--preset",
            type=str,
            choices=["major-india", "global-countries"],
            help="Seed a curated set of cities/countries instead of a single --city/--citycode or --country.",
        )
        parser.add_argument(
            "--limit",
            type=int,
            default=100,
            help="Max hotels to pull per city (TripJack Listing itself only ever sends the first 100 hids per search anyway). Default 100.",
        )
        parser.add_argument(
            "--popular",
            action="store_true",
            help="Mark seeded rows as is_popular=True (shown first in destination search).",
        )

    def handle(self, *args, **options):
        provider = (getattr(settings, "HOTEL_PROVIDER", "") or "").strip().lower()
        if provider != "tripjack":
            raise CommandError(
                "HOTEL_PROVIDER must be 'tripjack' to seed from live TripJack data "
                f"(currently '{provider or 'unset'}')."
            )

        client = TripJackHotelClient()
        if not client.is_configured():
            raise CommandError("TRIPJACK_API_KEY / HOTEL_HMS_BASE_URL / HOTEL_BOOKER_BASE_URL are not fully configured.")

        preset = options.get("preset")
        limit = options["limit"]
        is_popular = options["popular"]

        # Each target is (label, region_ids, country_name). Exactly one of
        # region_ids/country_name is set; the other stays None.
        targets = []
        if preset == "major-india":
            targets = [(name, [citycode], None) for name, citycode in MAJOR_INDIA_CITIES.items()]
        elif preset == "global-countries":
            targets = [(name.upper(), None, name) for name in GLOBAL_COUNTRIES]
        else:
            city = options.get("city")
            citycode = options.get("citycode")
            country = options.get("country")
            if city and citycode:
                targets = [(city.upper(), [citycode], None)]
            elif country:
                targets = [(country.upper(), None, country)]
            else:
                raise CommandError(
                    "Provide --city and --citycode together, or --country, "
                    "or --preset major-india / global-countries."
                )

        total_created = 0
        total_updated = 0

        for label, region_ids, country_name in targets:
            self.stdout.write(f"Fetching hotel mapping for {label}...")
            try:
                hotel_ids = self._fetch_hotel_ids(client, limit, region_ids=region_ids, country_name=country_name)
            except TripJackHotelError as exc:
                self.stderr.write(self.style.WARNING(f"  Skipping {label}: {exc}"))
                continue

            if not hotel_ids:
                self.stdout.write(self.style.WARNING(f"  No hotels returned for {label}."))
                continue

            self.stdout.write(f"  {len(hotel_ids)} hotel ID(s) found, fetching content...")
            # City-scoped targets pass their own label as city_name; country-scoped
            # targets pass None so _seed_hotels falls back to each hotel's own
            # response country (see _seed_hotels docstring note below).
            city_name = label if region_ids else None
            created, updated = self._seed_hotels(client, hotel_ids, city_name, is_popular, fallback_country=country_name)
            total_created += created
            total_updated += updated
            self.stdout.write(self.style.SUCCESS(f"  {label}: {created} created, {updated} updated."))

        self.stdout.write(self.style.SUCCESS(f"Done. {total_created} created, {total_updated} updated in total."))

    def _fetch_hotel_ids(self, client, limit, region_ids=None, country_name=None):
        hotel_ids = []
        page = 0
        page_size = min(limit, 100)
        # fetch-hotel-mapping's countryName filter is case-sensitive and only
        # matches TripJack's own ALL-CAPS country names - confirmed live:
        # "INDIA" -> 111707 hotels, "India" -> 5 (a coincidental partial match),
        # "india" -> 0. Not documented anywhere; discovered by direct probing.
        if country_name:
            country_name = country_name.upper()
        while len(hotel_ids) < limit:
            data = client.hotel_mapping(region_ids=region_ids, country_name=country_name, page=page, size=page_size)
            batch = [h["tjHotelId"] for h in data.get("hotels", [])]
            if not batch:
                break
            hotel_ids.extend(batch)
            pageable = data.get("pageable") or {}
            if page + 1 >= pageable.get("totalPages", page + 1):
                break
            page += 1
        return hotel_ids[:limit]

    def _seed_hotels(self, client, hotel_ids, city_name, is_popular, fallback_country=None):
        created = 0
        updated = 0

        for i in range(0, len(hotel_ids), 50):
            chunk = hotel_ids[i : i + 50]
            data = client.hotel_content(chunk)
            for hotel in data.get("hotels", []):
                tj_hotel_id = hotel.get("tjHotelId")
                name = hotel.get("name")
                if not tj_hotel_id or not name:
                    continue

                address = ((hotel.get("locale") or {}).get("address")) or {}
                country = (address.get("countryname") or fallback_country or "Unknown").title()
                # Country-scoped targets (city_name=None) have no per-hotel city:
                # TripJack's fetch-hotel-content response has no confirmed city-name
                # field in this codebase (only countryname/citycode are verified -
                # see hotel/providers/tripjack_client.py), so the country itself is
                # used as the coarser `city` value rather than guessing a field.
                resolved_city = city_name.title() if city_name else country
                image_url = self._pick_hero_image(hotel.get("images") or [])
                star_rating = self._parse_star_rating(hotel.get("star_rating"))

                _, was_created = Hotel.objects.update_or_create(
                    tj_hotel_id=str(tj_hotel_id),
                    defaults={
                        "name": name,
                        "city": resolved_city,
                        "country": country,
                        "image_url": image_url or "",
                        "star_rating": star_rating,
                        "is_popular": is_popular,
                        "is_active": bool(hotel.get("is_active", True)),
                    },
                )
                if was_created:
                    created += 1
                else:
                    updated += 1

        return created, updated

    @staticmethod
    def _parse_star_rating(raw_value):
        """TripJack sends star_rating as a numeric string, e.g. "4"."""
        try:
            rating = int(str(raw_value))
        except (TypeError, ValueError):
            return None
        return rating if 0 <= rating <= 7 else None

    @staticmethod
    def _pick_hero_image(images):
        """
        Picks one display URL from fetch-hotel-content's images[] array.
        Prefers the hero image (is_hero_image=True); within that image,
        prefers the "original" link, else the largest "<N>px" size key,
        else whatever link is present.
        """
        if not images:
            return None

        hero = next((img for img in images if img.get("is_hero_image")), images[0])
        links = hero.get("links") or {}
        if not links:
            return None

        if "original" in links:
            return (links["original"] or {}).get("href")

        def _px_size(key):
            digits = "".join(ch for ch in key if ch.isdigit())
            return int(digits) if digits else -1

        best_key = max(links, key=_px_size)
        return (links[best_key] or {}).get("href")
