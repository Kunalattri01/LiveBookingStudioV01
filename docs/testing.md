# Testing

Run the complete test suite with:

```text
python manage.py test
```

Before handing the project to another developer, also run:

```text
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py migrate
```

The foundation includes focused tests for accounts, wishlist, booking and notifications. Existing flight tests remain in place.
