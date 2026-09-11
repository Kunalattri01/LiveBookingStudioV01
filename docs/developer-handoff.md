# Developer Handoff

## Local setup

1. Create and activate a virtual environment.
2. Install `requirements.txt`.
3. Copy `.env.example` to `.env`.
4. Set a local Django secret key.
5. Add supplier credentials only to the local `.env` of the developer who needs them.
6. Run `python manage.py migrate`.
7. Run `python manage.py check`.
8. Run `python manage.py test`.
9. Start the server with `python manage.py runserver`.

## Project ownership by area

- `core/`: shared settings records, notifications and audit trail.
- `accounts/`: customer identity, profile, login and registration.
- `booking/`: supplier-neutral booking and payment records.
- `wishlist/`: saved travel items.
- `flight/`: flight search and TripJack adapter code.
- `hotel/`: hotel pages and the place where hotel integration will be added.
- `interactions/`: external integration helpers retained from the original project.
- `legal/`: public legal pages.
- `support/`: support page and future support workflow.
- `UserInterface/`: homepage entry point.

## Important rule for integrations

Supplier clients must not be imported directly into shared models or common UI. Put supplier calls behind an adapter/provider, normalize the response, and pass the normalized object to the application layer.

## Secrets

Never commit `.env`. Never put a supplier API key in a template, JavaScript file, test fixture, documentation page or migration. `.env.example` contains names and safe defaults only.

## CDN rule

External front-end libraries are declared once in `templates/base/public_base.html`. Individual templates should not add another copy of the same library. Page-specific CSS/JS belongs in the page template blocks or the `assets/` directory.


## Maintenance rules

- Keep supplier HTTP calls inside provider/client code.
- Keep supplier response mapping inside normalizers.
- Keep shared booking, account, wishlist and notification models supplier-neutral.
- Add new vertical-specific code under its own app instead of adding product logic to `core`.
- Keep shared browser libraries in `templates/base/public_base.html`; do not add duplicate CDN library tags to child templates.
- Real credentials belong in `.env` only.
- Run `python manage.py check`, `python manage.py makemigrations --check --dry-run`, and `python manage.py test` before handing changes to another developer.
