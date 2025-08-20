Valkey (session store)
-----------------------

This service can optionally use Valkey to persist refresh/session tokens. To enable Valkey in local development:

- Ensure `valkey` is present in `docker-compose.mvp.yml` (the repo includes a `valkey` service).
- Start the stack: `docker compose -f ../../docker-compose.mvp.yml up -d --build` from the repo root.
- `VALKEY_URL` will be injected into the `auth-service` container by the compose file. The format supported is:
  - `valkey://<host>:<port>/<db>` to use the native Python `valkey` client.

If you prefer an HTTP façade for Valkey, keep `VALKEY_URL` as `http(s)://...` and the session store will use the HTTP endpoints.
