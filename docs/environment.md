# Environment & local setup

## Environment variables

All read via `os.environ` in `MAIN/settings.py`, loaded from a local
`.env` file (via `python-dotenv`) if present. `.env` is git-ignored;
`.env.example` documents the shape with no real values.

| Variable | Default | Purpose |
|---|---|---|
| `DJANGO_SECRET_KEY` | dev-only fallback key | Django secret key. Must be set to a real random value in production. |
| `DJANGO_DEBUG` | `True` | `False` in production. |
| `DJANGO_ALLOWED_HOSTS` | `*` | Comma-separated host list; restrict in production. |
| `TRIPJACK_API_KEY` | `""` | TripJack API key (sandbox key currently stored locally in `.env` only). Never hardcoded, never logged, never returned in any response. |
| `TRIPJACK_BASE_URL` | `""` | TripJack API base URL. **Currently unknown/unset** - not provided, not guessed (see [tripjack-integration.md](tripjack-integration.md)). |
| `TRIPJACK_ENV` | `test` | `test` or `production` - informational; switching environments is meant to be a config change once the adapter is implemented. |
| `FLIGHT_PROVIDER` | `unconfigured` | Selects the active flight supplier. Only `tripjack` is a recognized real provider; every other value (including `unconfigured`) safely resolves to `UnconfiguredProvider`. There is no value that selects the mock provider. |

## Local setup

```bash
cd TripJack
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # then fill in real values as needed
python manage.py migrate
python manage.py runserver
```

Open `http://127.0.0.1:8000/` for the homepage.

## Migrations

Two migrations exist, both in the `flight` app:

- `0001_initial.py` - creates the `Airport` table (application master
  data only).
- `0002_seed_airports.py` - a data migration seeding ~15 airports/
  cities. Reversible (`migrate flight 0001` removes the seeded rows).

No other app has models or migrations yet. Running `migrate` is
idempotent and safe to re-run.

## Admin

`Airport` is registered in Django admin (`flight/admin.py`) so master
data can be added/edited/deactivated independently of any code change
or supplier integration. Create a superuser to access it:

```bash
python manage.py createsuperuser
```

### Email configuration

The project uses Django 6.1's `MAILERS` setting. Do not add the older `EMAIL_BACKEND` setting alongside it; Django 6.1 treats that combination as a configuration error.
