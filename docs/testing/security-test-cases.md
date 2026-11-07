# Security test cases

- Missing and incorrect ingestion key are rejected.
- Empty backend key fails closed for ingestion.
- Malformed payloads receive validation errors.
- Unsupported alert severity is rejected.
- Unapproved CORS origins are not granted browser access.
- Read endpoints are documented as unauthenticated until authorization is implemented; CORS is not access control.