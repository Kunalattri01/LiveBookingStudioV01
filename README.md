# Travel Platform — Common Backend Foundation

This repository contains the shared platform layer for a travel product. It is designed so flight, hotel, cab and future verticals can share account, booking, wishlist, notification and configuration services without sharing supplier-specific code.

## Main areas

| App | Purpose |
|---|---|
| `core` | Notifications, system settings, audit logs and small shared helpers |
| `accounts` | Registration, login, logout, profile and account API |
| `booking` | Supplier-neutral booking, booking items and payment transaction records |
| `wishlist` | Generic saved-item lists that can work with future travel models |
| `flight` | Flight search/provider/normalizer implementation |
| `hotel` | Hotel web flow placeholder for the hotel integration |
| `interactions` | External integration helpers retained from the original project |
| `legal` | Terms, privacy, refund and user agreement pages |
| `support` | Support page foundation |
| `UserInterface` | Homepage entry point |

## Quick start

```text
python -m venv .venv
# Windows: .venv\\Scripts\\activate
# Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
copy .env.example .env
python manage.py migrate
python manage.py check
python manage.py test
python manage.py runserver
```

## Environment

Keep real credentials in `.env`. The repository deliberately contains no real supplier key.

The flight timeout is configurable through `TRIPJACK_TIMEOUT_SECONDS`; the default is 22 seconds for local development.

## API base

Shared APIs are under `/api/v1/`.

- `/api/v1/accounts/`
- `/api/v1/booking/`
- `/api/v1/wishlist/`
- `/api/v1/core/`
- `/api/v1/` (existing flight API routes are included from `flight.api.urls`)

## Integration rule

Supplier clients belong behind provider/adaptor and normalizer layers. Shared apps should work with application-level models and DTOs, not raw supplier responses.

See `docs/developer-handoff.md` and `docs/common-platform-foundation.md` for the handoff notes.
