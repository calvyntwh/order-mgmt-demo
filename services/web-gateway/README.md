# Web Gateway

Run tests (inside service directory):

```bash
cd services/web-gateway
uv run pytest -q
```

Run locally:

```bash
cd services/web-gateway
uv run python -m uvicorn app.main:app --reload --port 8002
```

This gateway includes a tiny `/whoami` endpoint that proxies token introspection to the Auth service.
