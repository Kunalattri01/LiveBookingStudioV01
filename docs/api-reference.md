# API reference (v1)

Base path: `/api/v1/`

Both endpoints are currently **unauthenticated** (no login/auth exists
yet - authentication is a later phase). Do not rely on these for
anything beyond public search until authentication is added.

Neither endpoint reads from, or writes to, any flight-supplier data.
No search, fare, or availability data is ever persisted (see
[architecture.md](architecture.md#database-rules-unchanged-from-phase-1-still-enforced)).

---

## GET /api/v1/airports/

Airport/city autocomplete, backed entirely by our own local `Airport`
master data (never TripJack).

**Method:** `GET`
**Auth:** none
**Query parameters:**

| Param | Type | Required | Description |
|---|---|---|---|
| `q` | string | no | Free-text match against airport code, city, or airport name (case-insensitive substring). Omit or leave empty to get the default/popular list. |

**Response — 200 OK**

```json
{
  "results": [
    { "code": "DEL", "city": "New Delhi", "airport": "Indira Gandhi International Airport" },
    { "code": "BOM", "city": "Mumbai", "airport": "Chhatrapati Shivaji Maharaj International Airport" }
  ]
}
```

Up to 10 results, ordered by popularity then city name. No error
responses are defined for this endpoint beyond standard Django/DRF
5xx handling.

---

## POST /api/v1/flights/search/

Real flight-search entry point for web and mobile clients.

**Method:** `POST`
**Auth:** none (search itself is not gated; booking will be, in a
later phase)
**Content-Type:** `application/json`

**Request body**

One-way / round-trip:

```json
{
  "trip_type": "roundtrip",
  "origin": "DEL",
  "destination": "BOM",
  "departure_date": "2026-09-20",
  "return_date": "2026-09-27",
  "adults": 1,
  "children": 0,
  "infants": 0,
  "cabin_class": "economy",
  "special_fare": "regular"
}
```

Multi-city:

```json
{
  "trip_type": "multicity",
  "segments": [
    { "origin": "DEL", "destination": "BOM", "departure_date": "2026-09-20" },
    { "origin": "BOM", "destination": "BLR", "departure_date": "2026-09-24" }
  ],
  "adults": 1,
  "cabin_class": "economy"
}
```

| Field | Type | Notes |
|---|---|---|
| `trip_type` | string | `oneway`, `roundtrip`, or `multicity` |
| `origin` / `destination` | string | IATA code; required for `oneway`/`roundtrip`, ignored for `multicity` |
| `departure_date` / `return_date` | string (`YYYY-MM-DD`) | `return_date` only used/required for `roundtrip` |
| `segments` | array | required for `multicity`; 2–6 entries, each `{origin, destination, departure_date}`, dates must be chronological |
| `adults` | int | 1–9 |
| `children` | int | 0–9 |
| `infants` | int | 0 to `adults` |
| `cabin_class` | string | `economy`, `premium_economy`, `business`, `first` |
| `special_fare` | string | free-form, defaults to `"regular"`; not currently validated against a fixed list |

**Response — 200 OK** (now real for one-way searches when
`FLIGHT_PROVIDER=tripjack` - see
[tripjack-integration.md](tripjack-integration.md) for exactly what's
verified)

```json
{
  "success": true,
  "flights": [
    {
      "provider": "tripjack",
      "provider_reference": "142",
      "segments": [
        {
          "segment_id": "142",
          "airline_code": "6E",
          "airline_name": "IndiGo",
          "is_lcc": true,
          "flight_number": "5341",
          "aircraft_type": "321",
          "origin": "DEL",
          "origin_city": "Delhi",
          "origin_terminal": "Terminal 3",
          "destination": "GOI",
          "destination_city": "Goa In",
          "destination_terminal": null,
          "departure_time": "2026-09-21T05:10",
          "arrival_time": "2026-09-21T07:40",
          "duration_minutes": 150,
          "technical_stops": 0,
          "stopovers": []
        }
      ],
      "stops": 0,
      "total_duration_minutes": 150,
      "fares": [
        {
          "fare_id": "5-0019138363_0DELGOI6E5341~1211081761086558",
          "fare_type": "UPFRONT",
          "cabin_class": "ECONOMY",
          "booking_class": "O",
          "fare_basis": "RLIP",
          "base_fare": 7325.0,
          "taxes": 2585.5,
          "total_fare": 9910.5,
          "net_fare": 9910.5,
          "currency": null,
          "seats_available": 9,
          "meal_included": false,
          "refundable": null,
          "refund_type_code": 1,
          "baggage": { "cabin": "7 Kg", "checkin": "15 Kg (01 Piece only)" },
          "fare_rules_reference": null
        }
      ]
    }
  ]
}
```

Note `currency`, `refundable`, and `fare_rules_reference` are `null` -
these are genuinely absent/unconfirmed in the verified TripJack
response, not omitted by mistake. See
[tripjack-integration.md](tripjack-integration.md#what-is-deliberately-not-implemented-and-why).

**Response — 400 Bad Request** (validation failure)

```json
{
  "success": false,
  "error_code": "invalid_search_request",
  "error_message": "Unknown departure airport code: XXX."
}
```

**Response — 501 Not Implemented** (round-trip or multi-city with
`FLIGHT_PROVIDER=tripjack` - the request shape isn't verified, so no
network call is attempted)

```json
{
  "success": false,
  "error_code": "provider_search_not_supported",
  "error_message": "TripJack integration currently supports only one-way search. 'roundtrip' response handling is unverified and not implemented - see docs/tripjack-integration.md."
}
```

**Response — 502 Bad Gateway** (TripJack call failed: timeout,
connection error, non-200 HTTP status, malformed response, or
TripJack reported failure)

```json
{
  "success": false,
  "error_code": "flight_provider_error",
  "error_message": "TripJack request timed out."
}
```

**Response — 503 Service Unavailable** (`FLIGHT_PROVIDER` unset/
`unconfigured`/unrecognized - no provider at all)

```json
{
  "success": false,
  "error_code": "flight_provider_not_configured",
  "error_message": "No flight provider is configured. Set FLIGHT_PROVIDER to a supported value (currently: 'tripjack') once TripJack credentials/documentation are available."
}
```

**This endpoint never returns HTTP 200 with synthetic/fake flight
data**, under any `FLIGHT_PROVIDER` value.

---

## OpenAPI/Swagger

Not generated in this phase. The request/response shapes above are
stable enough to generate an OpenAPI schema from once the TripJack
adapter is real (so the `NormalizedFlight` example fields reflect an
actually-achievable response rather than a hypothetical one). Adding
`drf-spectacular` or similar is a small, low-risk addition for a later
phase once there's real data flowing through the success path.
