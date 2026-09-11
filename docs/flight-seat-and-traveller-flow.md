# Flight Traveller and Seat Selection Flow

This note describes the current web flow from fare selection to seat selection.

## Passenger count

The search request determines the passenger list. Adults, children and infants are expanded into individual traveller records. The traveller page renders one form section for every traveller and sends the complete list to the server before the seat page opens.

## Server-side storage

Traveller details are kept in the Django session under `flight_travellers`. Seat selections are kept under `selected_seats`. This is flow state for the current booking session; it is not a permanent passenger database.

## Seat assignment

A seat is assigned to a specific passenger. The browser requires one seat per traveller before continuing. The API validates the same rule on the server and rejects duplicate passenger assignments, duplicate seat codes and incomplete passenger assignments.

The supplier seat map remains the source of truth for whether an individual seat is selectable. The frontend only enables seats that the normalized API response marks as both available and availability-known.

## Supplier boundary

The browser never calls the supplier directly. The path remains:

`Browser -> application API -> booking provider manager -> supplier adapter -> supplier client -> normalizer -> application DTO -> Browser`

Any supplier-specific field conversion belongs in the provider normalizer. Do not add supplier URLs or supplier response parsing to templates or JavaScript.

## UI sizing

The seat map is intentionally compact so the complete cabin can normally be viewed without a long vertical page. On narrow screens the cabin may scroll horizontally rather than forcing the whole page to become excessively tall.
