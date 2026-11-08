# SQLite schema migration

Startup performs additive migration for the alert `status` and `updated_at` columns and creates the `alert_activity` table if absent. Existing alert rows receive status `new`. Back up the database before deployment, test migration against a copy, verify row counts and retain a rollback copy. Do not replace a production database with a test fixture.