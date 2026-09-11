# Common Platform Foundation

This project now contains the shared backend pieces that can be used by flights, hotels, cabs and future travel modules.

## What is shared

### Accounts
- Django's built-in User model remains the identity source.
- `accounts.UserProfile` stores travel preferences and contact information that do not belong in the core user table.
- Browser login, registration, logout and profile pages are available.
- Session-based API endpoints are available under `/api/v1/accounts/`.
- The account API only exposes the logged-in user's data.

### Booking
The `booking` app is supplier-neutral. It stores the application booking record without knowing whether the inventory came from TripJack, a hotel supplier, a cab supplier or another vendor.

Main models:
- `Booking`: the customer-facing booking record.
- `BookingItem`: individual fare, room, transfer or other booking components.
- `PaymentTransaction`: payment lifecycle information. It is a record of a payment attempt/result, not a payment gateway implementation.

The actual supplier or payment gateway integration should stay in a provider/service layer. Do not put supplier-specific fields throughout the shared booking models.

### Wishlist
Wishlist items use Django content types so a saved item can point at a flight, hotel, destination or another future model without changing the wishlist schema every time a new vertical is added.

### Notifications and common utilities
The `core` app contains:
- `Notification` for user-facing messages.
- `SystemSetting` for simple admin-managed configuration.
- `AuditLog` for a lightweight record of important business actions.
- small helpers for decimal conversion, notifications and audit records.

## API examples

Authentication uses Django sessions. For local development, the browser can use the normal login page. API clients can call:

- `POST /api/v1/accounts/register/`
- `POST /api/v1/accounts/login/`
- `POST /api/v1/accounts/logout/`
- `GET /api/v1/accounts/me/`
- `GET/PATCH /api/v1/accounts/api/users/<id>/`

Shared resources:

- `GET/POST/PATCH /api/v1/booking/bookings/`
- `POST /api/v1/booking/bookings/<id>/cancel/`
- `GET /api/v1/booking/payments/`
- `GET/POST /api/v1/wishlist/lists/`
- `GET/POST /api/v1/wishlist/items/`
- `GET/PATCH /api/v1/core/notifications/`

## What this foundation intentionally does not do

- It does not implement a real payment gateway.
- It does not invent supplier inventory.
- It does not copy TripJack fields into common models.
- It does not store raw flight search responses as permanent application data.
- It does not force hotel or flight developers to use the same supplier.

## Working with the hotel developer

Share the common apps (`accounts`, `booking`, `wishlist`, `core`), the base template, common assets and the documentation. Give the hotel developer the hotel app and its supplier integration separately. The flight provider credentials should remain private to the flight integration environment.

## Adding a new vertical

1. Create the vertical app and its supplier/provider layer.
2. Normalize supplier responses into the vertical's internal DTOs.
3. Use the shared `Booking` model when the customer confirms a purchase.
4. Use `Notification` for customer messages.
5. Use `WishlistItem` when the vertical needs saved items.
6. Record important business actions in `AuditLog`.

This keeps the common layer stable while individual verticals evolve independently.
