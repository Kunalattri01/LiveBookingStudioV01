# Architecture

The application is split into shared platform services and travel verticals.

```text
Browser / Mobile API client
        |
        +--> accounts / authentication
        +--> core / notifications / settings / audit
        +--> wishlist / saved items
        +--> booking / booking + payment records
        |
        +--> flight -> provider -> normalizer -> internal DTO
        |
        +--> hotel -> hotel provider -> normalizer -> internal DTO
```

The shared booking layer deliberately stores application-level information. Supplier-specific request/response structures stay in the relevant provider package.

For flights, the existing provider/normalizer boundary is preserved. A future hotel provider should follow the same idea so a supplier change does not require rewriting the customer-facing booking API.
