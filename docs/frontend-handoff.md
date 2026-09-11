# Frontend / UI-UX developer handoff

This document describes the **API contracts** available for building
a new frontend. It intentionally prescribes nothing about visual
design, layout, component structure, or styling - that's for the
UI/UX designer to decide. It also does not require the new frontend to
be built any particular way (React, plain JS, server-rendered, mobile
native) - the API is framework-agnostic JSON over HTTP.

## What you can build against today

### 1. Airport/city autocomplete

`GET /api/v1/airports/?q=<text>`

Returns up to 10 matches from our own airport/city master data (not
live supplier data - this never changes based on flight availability).
See [api-reference.md](api-reference.md#get-apiv1airports) for the
exact response shape.

### 2. Flight search

`POST /api/v1/flights/search/`

Accepts one-way, round-trip, or multi-city (2–6 segments) search
requests. See [api-reference.md](api-reference.md#post-apiv1flightssearch)
for the full request/response contract.

**Important - build your UI to handle this today:** this endpoint
currently always returns `HTTP 503` with
`error_code: "flight_provider_not_configured"` for any structurally
valid search, because the real flight-supplier integration isn't
finished yet (see [tripjack-integration.md](tripjack-integration.md)).
This is not a bug and not temporary downtime - it's the correct,
honest response until a real provider is wired up. Your UI should
treat `503` + this error code as an expected "search is not live yet"
state (e.g. a clear "search is temporarily unavailable" message),
distinct from a `400` (the user's input was invalid - show them why)
or a genuine server error.

Once TripJack (or another provider) is implemented, the response shape
on success is already defined and will not change - see the `200 OK`
example in the API reference. You can safely build result-list UI
against that shape now.

## What is explicitly out of scope for the API right now

- No booking, fare-selection, traveller-detail, or payment endpoints
  exist yet.
- No authentication exists yet. Don't build login-gated flows against
  this API yet.
- No pagination on flight search results yet (not needed until real
  results exist).

## Multi-city

The API fully supports multi-city today (2–6 segments, validated
chronologically). The *current* homepage widget's UI doesn't have a
segment-entry interface, so it doesn't send multi-city requests - but
that's a frontend gap, not an API limitation. A new frontend can
implement multi-city search UI against `/api/v1/flights/search/`
immediately.

## Stability

Fields in the `NormalizedFlight`/`FareOption` response shape
(`flight/services/dto.py`) will only ever be `null`/absent, never
guessed or fabricated, if a supplier doesn't provide a value - build
your UI to handle missing fields gracefully rather than assuming every
field is always populated.
