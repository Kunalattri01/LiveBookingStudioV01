# Flight Booking Flow - UI and Availability Update

## What changed

### 1. Modify Search stays on the results page
`Modify Search` now opens an in-page modal. It supports one-way, round-trip and multi-city searches, uses the local Airport master data for airport suggestions, and builds a new `/flight/results/` URL after validation.

### 2. Seat map is easier to read
The seat map uses four clear states:

- Green border / white seat: explicitly available
- Blue seat: selected by the current user
- Dark slate seat: explicitly unavailable
- Light slate seat: availability is unknown and cannot be selected

The UI does not turn an unknown seat into an available seat.

### 3. Supplier boundary is preserved
Browser code calls only application endpoints under `/api/v1/flights/`. Supplier HTTP calls stay inside the provider adapter/client layer. Supplier response fields are converted by the normalizers before they reach templates or browser code.

### 4. Session keys are provider-neutral
The review and seat-map session values are stored as `flight_review` and `flight_seat_map`, rather than supplier-specific session names. This keeps the booking flow independent of the current flight vendor.

## Round-trip and multi-city

The existing search validator represents round-trip searches as two internal journey segments and multi-city searches as two to six segments. The results UI already groups normalized results by `leg_label` and requires a selection for every returned journey leg before fare review.

The actual supplier response must contain a corresponding leg for the search. The application does not manufacture a missing leg or invent supplier fields.

## Testing performed for this update

- JavaScript syntax checked with Node for the changed result and seat-map scripts.
- Python source compiled with `compileall`.
- Supplier imports were checked to ensure application views/templates do not call the supplier client directly; supplier-specific calls remain in the provider/client boundary and supplier-focused tests.

A full Django test run still requires the project's Python dependencies to be installed in the execution environment.


## Inventory and result loading

The flight-search API does not slice or paginate the supplier response. `FlightSearchApiView`
serializes every `NormalizedFlight` returned by `FlightService`. The browser stores that complete
array in `allFlights` and progressively renders it in batches controlled by `FRONTEND_PAGE_SIZE`.
The infinite scroll is therefore a presentation optimization, not a reduction of inventory.

The supplier search modifier is now configurable through:
- `TRIPJACK_INCLUDE_DIRECT_FLIGHTS`
- `TRIPJACK_INCLUDE_CONNECTING_FLIGHTS`

Both default to `True` in the development configuration. This broadens the search beyond the
previous direct-only request. It still cannot guarantee that the supplier dashboard and our result
count are identical: supplier-side inventory, account permissions, fare visibility, timing, caching,
or additional dashboard filters can change the result set. The application never invents missing
flights.

## Traveller data

Traveller details are submitted to `/api/v1/flights/traveller/` and stored in Django's server-side
session. They are no longer stored only in browser `sessionStorage`. The form is generated for every
adult, child and infant in the search request, so a booking for five passengers collects five
traveller records. Passport/nationality fields remain conditional on the normalized review response.

This is a booking-flow draft store, not the final permanent booking record. Permanent booking and
payment persistence should happen when the actual booking transaction is implemented.

## Seat-map availability

The supplied TripJack seat-map example uses:
- `seatNo`
- `seatPosition.row`
- `seatPosition.column`
- `isBooked`
- `isAisle`
- `amount`
- `code`

The normalizer now maps those fields explicitly. `isBooked: false` becomes a normalized available
seat; `isBooked: true` becomes unavailable. This fixes the earlier situation where valid seats were
treated as unknown because the normalizer was looking for `isAvailable` instead.

The browser still only enables seats where the normalized response says `available === true` and
`availability_known === true`. No seat is enabled based only on the fare's `sR` ("seats remaining")
value.

## Supplier boundary

Browser templates and JavaScript contain no TripJack endpoint, API key, or supplier-specific field
names. Supplier HTTP calls remain in `interactions/tripjack/client.py`; provider adapters call the
client and immediately normalize the result before returning it to application services/API views.
A future supplier can implement the same provider-neutral interfaces without changing the browser
contract.

## MakeMyTrip-inspired flow

The current flow follows the same broad consumer-booking pattern found in public MakeMyTrip material:
search -> choose flight -> enter traveller details -> seat selection -> later booking/payment.
MakeMyTrip also documents filling required details for all passengers and seat selection for
multiple passengers. This project intentionally does not copy proprietary UI or implementation.
