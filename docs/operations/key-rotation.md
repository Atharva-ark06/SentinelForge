# Ingestion key rotation

1. Generate a new high-entropy key using a cryptographically secure random generator.
2. Update the backend secret store and every trusted sensor/loader environment.
3. Restart/redeploy affected processes in a coordinated window.
4. Verify authorized ingestion and rejection of the previous key.
5. Revoke the old value and review logs for unexpected use.

Never commit keys or place them in `VITE_*` variables.