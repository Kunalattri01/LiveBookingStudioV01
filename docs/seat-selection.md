# Seat selection implementation

## Data flow

The browser never calls TripJack directly.

1. Fare review is requested through `/api/v1/flights/review/`.
2. `FlightReviewApiView` resolves the active `FlightBookingProvider`.
3. `TripJackBookingAdapter` calls `TripJackClient` and immediately passes the raw response to `TripJackBookingNormalizer`.
4. The normalized review is stored in the server session.
5. `/api/v1/flights/seat-map/` repeats the same provider -> client -> normalizer flow.
6. The browser receives only provider-neutral seat data.

## Availability and the "9 seats" question

The fare/search response may report an inventory value such as `9 seats`. That number is not silently used to create nine or fewer seat-map buttons. Seat-map availability is a separate supplier response.

The UI therefore follows two rules:

- A seat is selectable only when the normalized seat explicitly says `available: true` and `availability_known: true`.
- A seat with unknown availability is shown for physical layout context but is disabled.

This avoids allowing a user to select a seat merely because a fare advertised a remaining-inventory count.

## Aircraft-style presentation

When the supplier supplies row/column information, the UI groups seats by row, creates a center aisle, and displays the cabin from the front/cockpit toward the tail. When row/column values are omitted but the seat code is in a standard form such as `12A`, the normalizer derives row `12` and column `A` purely for layout. It does not invent availability, pricing, or seat types.

If the supplier response lacks enough structural information to draw a trustworthy layout, the UI does not fabricate a grid.

## Future supplier replacement

A future supplier must implement `FlightBookingProvider` and a matching booking normalizer. The API and browser contract should remain unchanged.
