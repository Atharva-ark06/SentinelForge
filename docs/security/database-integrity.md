# Database integrity

Restrict database file permissions to the service account, keep it outside the public web root, use durable storage, back up consistently and test restoration. Monitor disk capacity and database errors. Do not share a writable SQLite file between unrelated application instances without an appropriate concurrency/storage design.