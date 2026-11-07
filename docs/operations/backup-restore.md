# SQLite backup and restore

Use a consistent SQLite backup method (for example, the SQLite online backup API) rather than copying a live database file while writes are occurring. Store backups outside the web root, encrypt them at rest, restrict access and test restoration periodically. A temporary hosting filesystem is not durable storage.