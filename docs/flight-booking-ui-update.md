# Flight booking flow update

## What changed

The flight result flow now keeps fare selection on the results page.

1. Search results are loaded from `/api/v1/flights/search/`.
2. The user selects one flight for each required journey leg.
3. When all required legs are selected, a fare-selection modal opens on the same page.
4. The user selects the fare for each leg in the modal.
5. The browser saves the normalized selection through `/api/v1/flights/selection/`.
6. The fare is revalidated through `/api/v1/flights/review/`.
7. On successful review, the user moves to `/flight/traveller/`.
8. Traveller information is collected and the flow moves to `/flight/seat-selection/`.
9. Seat-map requests still use the provider adapter and booking normalizer. The browser never calls TripJack directly.

## Files changed

- `templates/flight/flights.html`
- `assets/js/flight-results.js`
- `assets/css/flights.css`
- `templates/flight/traveller.html`
- `assets/js/flight-traveller.js`

## New file

- `assets/css/flight-traveller.css`
- `docs/flight-booking-ui-update.md`

## Seat availability note

The application intentionally does not turn a fare-level inventory count such as "9 seats left" into nine selectable seats. A seat is selectable only when the normalized seat-map response explicitly marks it as available.

This is important because fare inventory and seat-map inventory are separate pieces of supplier data. If every seat is disabled while the fare says seats remain, inspect the normalized `/api/v1/flights/seat-map/` response. If the supplier's availability field is not being recognized, the TripJack booking normalizer must be updated using the actual UAT seat-map response. Do not enable seats by position or by the fare count.

## Safe testing

Run:

```text
python manage.py check
python manage.py test
```

For JavaScript syntax:

```text
node --check assets/js/flight-results.js
node --check assets/js/flight-traveller.js
node --check assets/js/flight-seat-selection.js
```


## Current flow notes

### Modify Search
The results page now opens an in-page search editor. It keeps the user on the results experience and submits a validated results URL for one-way, round-trip, or multi-city searches. Airport suggestions come from the local `flight` Airport master table.

### Seat map
Seat colors are intentionally high-contrast: green/white means explicitly available, blue means selected, dark slate means unavailable, and light slate means the supplier did not provide a reliable availability value. The browser never converts an unknown seat into an available seat.

### Supplier boundary
The browser calls only the application's `/api/v1/flights/*` endpoints. Supplier field names and supplier HTTP calls remain inside the provider/adapter and normalizer layers.
