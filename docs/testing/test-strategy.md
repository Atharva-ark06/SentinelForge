# Test strategy

Use unit tests for detection logic, API tests for schema/authentication/error paths, and integration tests with a temporary database. Keep all test events synthetic. Add regression tests for every reported bug and run frontend production builds plus backend tests in CI.