# TripJack integration status

## Current status: one-way search implemented and unit-verified

The project owner captured a real, successful TripJack UAT request/
response via Postman. That verified request/response is the sole
source of truth for everything below - nothing here is guessed.

**Verified UAT endpoint:**

```
POST https://apitest.tripjack.com/fms/v1/air-search-all
```

**Authentication:** `apikey` request header (not `Authorization:
Bearer`). The key is read from `TRIPJACK_API_KEY` (environment
variable / local `.env` only - never hardcoded, never logged, never
returned in any API response).

**Verified request (one-way, 2 adults, economy, direct flights
only):**

```json
{
  "searchQuery": {
    "cabinClass": "ECONOMY",
    "paxInfo": { "ADULT": "2", "CHILD": "0", "INFANT": "0" },
    "routeInfos": [
      {
        "fromCityOrAirport": { "code": "DEL" },
        "toCityOrAirport": { "code": "GOI" },
        "travelDate": "2026-09-21"
      }
    ],
    "searchModifiers": { "isDirectFlight": true, "isConnectingFlight": false }
  }
}
```

Implemented in `TripJackAdapter._build_search_payload()`
(`flight/providers/tripjack_provider.py`), unit-tested in
`flight/tests/test_tripjack_request_mapping.py` against this exact
shape.

**Verified response** (trimmed sample kept as a test fixture at
`flight/tests/fixtures/tripjack_air_search_all_sample.json`, no
secrets in it) normalizes into our internal `NormalizedFlight`/
`FareOption`/`FlightSegment` via `TripJackNormalizer`
(`flight/normalizers/tripjack.py`). Full field-provenance mapping is
documented on the dataclasses themselves in `flight/services/dto.py`.

## What is implemented

- One-way search: request mapping, HTTP call (`TripJackClient.search_flights`
  in `interactions/tripjack/client.py`), and normalization - all
  unit-tested (mocked HTTP layer for client/adapter tests; the
  normalizer is tested against the real captured response).
- Error handling: timeout, connection failure, non-200 HTTP status,
  malformed/non-JSON response, and a `status.success != true` response
  all raise `TripJackRequestError` -> wrapped as `ProviderUpstreamError`
  -> surfaced by the API as `HTTP 502` with `error_code:
  "flight_provider_error"`. No raw exception detail, headers, or the
  API key are ever included in that response.
- `FLIGHT_PROVIDER=tripjack` now actually attempts a real TripJack
  call for one-way searches.

## What is deliberately NOT implemented (and why)

- **Round-trip and multi-city.** TripJack's `routeInfos` field is
  documented (by the verified example) as an array, which could
  plausibly accept multiple legs for multi-city, and a round-trip
  might work the same way or might return a second `RETURN` key
  alongside `ONWARD` in `tripInfos`. We have no verified sample for
  either case, so we do not know the actual request or response shape
  TripJack uses, and guessing was explicitly ruled out. Calling
  `TripJackAdapter.search()` with `trip_type` other than `oneway`
  raises `ProviderUnsupportedRequestError` immediately - **no network
  call is attempted** (see `test_no_network_call_attempted_for_roundtrip`).
  This surfaces as `HTTP 501 provider_search_not_supported` from the
  API.
- **Connecting flights.** The verified request hardcodes
  `isDirectFlight: true, isConnectingFlight: false`. We don't know what
  other combinations return or whether they're valid, so every search
  currently requests direct flights only, regardless of what the user
  asked for. This is a known limitation.
- **`refundable` (boolean).** The response includes an `rT` field
  (`0` or `1`) that is clearly some kind of refund-type indicator, but
  its direction (does `1` mean refundable or not?) is not documented
  anywhere we have access to. Rather than guess, `FareOption.refundable`
  stays `None` and the raw value is preserved in
  `FareOption.refund_type_code` for whoever can confirm the semantics
  later.
- **`currency` and `fare_rules_reference`.** Neither field appears
  anywhere in the verified response, so both stay `None` - not
  defaulted to an assumed currency (e.g. INR) or a fabricated
  reference.
- **Fare revalidation, booking, cancellation, or any other TripJack
  endpoint.** Only `air-search-all` has been verified. No other
  endpoint path, request, or response shape is known.

## Live UAT call: NOT performed by this environment

Step 8 of this phase asked for one controlled live UAT call. This
sandboxed development environment's network egress is restricted to
an explicit allowlist (package registries, GitHub, etc.) and
`apitest.tripjack.com` is not on it - confirmed directly:

```
$ curl -i https://apitest.tripjack.com/fms/v1/air-search-all
HTTP/2 403
x-deny-reason: host_not_allowed
Host not in allowlist: apitest.tripjack.com. Add this host to your
network egress settings to allow access.
```

This is our own environment's proxy rejecting the request before it
reaches TripJack - not a TripJack error, and no credential was
transmitted anywhere. **All TripJack-facing code is implemented and
unit-tested against the real verified request/response, but the
actual live network round-trip has not been executed by this
environment.**

To run the live check yourself locally (outside this sandbox), with
your `.env` configured (`TRIPJACK_API_KEY`, `TRIPJACK_BASE_URL=https://apitest.tripjack.com`,
`FLIGHT_PROVIDER=tripjack`):

```bash
python manage.py shell -c "
from datetime import date
from flight.services.dto import SearchRequest, FlightSegmentRequest
from flight.services.flight_service import FlightService

req = SearchRequest(
    trip_type='oneway',
    segments=[FlightSegmentRequest(origin='DEL', destination='GOI', departure_date=date(2026, 9, 21))],
    adults=2,
)
result = FlightService().search(req)
print('success:', result.success)
print('num flights:', len(result.flights))
print('error:', result.error_code, result.error_message)
"
```

or via the API once the dev server is running:

```bash
curl -s -X POST http://127.0.0.1:8000/api/v1/flights/search/ \
  -H "Content-Type: application/json" \
  -d '{"trip_type":"oneway","origin":"DEL","destination":"GOI","departure_date":"2026-09-21","adults":2,"cabin_class":"economy"}'
```

Please report back the result (HTTP status + whether flights were
returned) - if it doesn't match the mocked-test expectations, that
would indicate the sandbox differs from what Postman captured (e.g.
inventory changed, or a header/detail Postman added implicitly that
wasn't visible in the exported request).

## Environment configuration

```
TRIPJACK_API_KEY=<your sandbox key>       # secret, .env only
TRIPJACK_BASE_URL=https://apitest.tripjack.com   # verified, not secret
TRIPJACK_ENV=test
FLIGHT_PROVIDER=tripjack   # or "unconfigured" to force the safe controlled error
```

## Remaining TripJack documentation needed for future phases

- Round-trip and multi-city request/response shape (sample
  responses).
- Fare revalidation endpoint (needed before booking - prices shown at
  search time cannot be assumed valid).
- Booking endpoint, request/response shape, and how the `id` fields
  captured here (`FareOption.fare_id`, `FlightSegment.segment_id`) are
  meant to be reused for booking.
- Confirmed semantics of `rT` (refundable direction).
- Confirmed currency (the response never states one).
- Cancellation/refund endpoints.

## Flight booking-flow extension

The application now exposes provider-independent steps after search selection:

1. Results selection is stored server-side in the Django session.
2. The selected fare IDs are sent to TripJack `POST /fms/v1/review` for review/revalidation.
3. A successful review stores the returned booking identifier in the session.
4. Traveller details are collected in a dedicated page; passport fields are shown when the review response explicitly exposes a passport-required flag.
5. Seat-map retrieval is available through TripJack `POST /fms/v1/seat` after review.

The seat-map response is deliberately treated defensively because the supplied Postman collection documents the endpoint but does not contain a representative response body. The UI will not fabricate seats when the supplier response cannot be safely interpreted.

### Search result loading

The results API continues to return every flight option supplied by TripJack in a successful search response. The browser renders those normalized results in small batches (15 at a time) using an `IntersectionObserver`, so the page remains responsive while the user scrolls. This is client-side progressive rendering, not a claim that TripJack provides server-side pagination. If TripJack itself returns fewer options, the application cannot invent additional inventory.

### Timeout configuration

The TripJack HTTP timeout is controlled by `TRIPJACK_TIMEOUT_SECONDS` and defaults to `22`. Set it in the local `.env` without changing application code.

## Hotel catalog: local snapshot, refreshed on a schedule

The `Hotel` table (`hotel/models.py`) is a local cache, not a live
mirror of TripJack. Destination search (`hotel/services/validators.py`,
`GET /api/v1/hotels/destinations/`) resolves a typed city/country to
TripJack `hids` by querying **only this local table** - never a live
TripJack call - because TripJack's Listing API v3 only accepts explicit
`hids` and its own fetch-hotel-mapping endpoint ignores free-text
`cityName`/`regionName` filters (confirmed by live probing; only
`countryName` and numeric `regionIds` actually filter it - see
`hotel/providers/tripjack_client.py`).

To keep that snapshot from going stale, `python manage.py
sync_tripjack_catalog` re-runs the `major-india` and `global-countries`
seed presets against the live, verified fetch-hotel-mapping /
fetch-hotel-content endpoints. It's idempotent (`update_or_create`), so
running it repeatedly is safe. Wire it into whatever scheduler the
deployment actually uses - there's no scheduling library in this
project's `requirements.txt` (no Celery/APScheduler), so the simplest
option is a plain cron entry, e.g. daily at 03:00:

```
0 3 * * * cd /path/to/project && /path/to/project/.venv/bin/python manage.py sync_tripjack_catalog >> /var/log/tripjack_sync.log 2>&1
```

**Known limitation:** TripJack's v3 partner reference documents a
Hotel Mapping *Sync* and a Deleted Mapping Sync endpoint, but neither
has ever been called or verified in this codebase - only the full
fetch-hotel-mapping/fetch-hotel-content pull has. So this scheduled
refresh only adds/updates hotels; it cannot detect or deactivate a
hotel TripJack has delisted. A truly complete sync (including
deletions) needs someone to confirm the Sync/Deleted-Mapping-Sync
request/response shape first - not guessed here.
