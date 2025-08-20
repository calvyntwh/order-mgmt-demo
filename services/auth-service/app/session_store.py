import json
import os
import time
import uuid
from typing import Any
from urllib.parse import urlparse

import httpx

# Defer importing the optional `valkey` library until runtime to avoid static
# analysis errors when the dependency isn't installed in the editor environment.
# Attempt a best-effort import here so runtime in containers uses the native
# client when available; otherwise leave `valkey` as None and fall back to
# HTTP-mode or the in-memory store.
try:
    import valkey as _valkey_module  # type: ignore
except Exception:
    _valkey_module = None

valkey = _valkey_module


class SessionStore:
    """Pluggable session store interface.

    Methods are intentionally synchronous to match the current auth-service
    codebase. Implementations should provide process-safe, durable storage.
    """

    def store_refresh_token(
        self, refresh_token: str, session_data: dict[str, Any], ttl_seconds: int
    ) -> None:
        raise NotImplementedError()

    def rotate_refresh_token(self, old_token: str, ttl_seconds: int) -> str | None:
        """Atomically rotate a refresh token across processes.

        Return the new refresh token on success, or None on failure (e.g., if
        the old token is missing/revoked).
        """
        raise NotImplementedError()

    def revoke_refresh_token(self, refresh_token: str) -> None:
        raise NotImplementedError()

    def is_refresh_revoked(self, refresh_token: str) -> bool:
        raise NotImplementedError()

    def get_session(self, refresh_token: str) -> dict[str, Any] | None:
        raise NotImplementedError()


class InMemorySessionStore(SessionStore):
    """Simple in-memory session store (single-process)."""

    def __init__(self) -> None:
        # refresh_token -> session record
        self._store: dict[str, dict[str, Any]] = {}

    def store_refresh_token(
        self, refresh_token: str, session_data: dict[str, Any], ttl_seconds: int
    ) -> None:
        self._store[refresh_token] = {
            "data": session_data,
            "expires_at": time.time() + ttl_seconds,
        }

    def rotate_refresh_token(self, old_token: str, ttl_seconds: int) -> str | None:
        rec = self._store.get(old_token)
        if not rec:
            return None
        # revoke old, create new
        new_token = uuid.uuid4().hex
        self._store.pop(old_token, None)
        self._store[new_token] = {
            "data": rec["data"],
            "expires_at": time.time() + ttl_seconds,
        }
        return new_token

    def revoke_refresh_token(self, refresh_token: str) -> None:
        self._store.pop(refresh_token, None)

    def is_refresh_revoked(self, refresh_token: str) -> bool:
        rec = self._store.get(refresh_token)
        if not rec:
            return True
        if rec.get("expires_at") and rec["expires_at"] < time.time():
            # expired => treat as revoked
            self._store.pop(refresh_token, None)
            return True
        return False

    def get_session(self, refresh_token: str) -> dict[str, Any] | None:
        if self.is_refresh_revoked(refresh_token):
            return None
        return self._store.get(refresh_token, {}).get("data")


class ValkeySessionStore(SessionStore):
    """Valkey-backed session store.

    This implementation assumes a simple HTTP API exposed by Valkey. The
    exact endpoint shapes are an implementation detail for the Valkey
    deployment; here we make reasonable assumptions and expose a thin client
    that can be adapted if the Valkey API differs.

    Assumptions (configurable):
    - VALKEY_URL: base URL for the Valkey service (e.g. https://valkey:8200)
    - VALKEY_API_KEY: optional API key passed in Authorization header

    API end points (assumed):
    - POST {base}/sessions -> create mapping (body: {refresh_token, session, ttl})
    - POST {base}/sessions/rotate -> rotate mapping (body: {old_token, ttl}) -> returns {new_token}
    - POST {base}/sessions/revoke -> revoke mapping (body: {token})
    - GET {base}/sessions/{token} -> returns {session} or 404

    If your Valkey deployment exposes different paths, adapt this class.
    """

    def __init__(
        self, base_url: str, api_key: str | None = None, timeout: int = 5
    ) -> None:
        # Support two Valkey URL forms for flexibility:
        # - HTTP-based control plane (http(s)://host:port) -> fall back to HTTP client
        # - native valkey URL (valkey://host:port/db) -> use valkey-py client
        self.timeout = timeout
        self.api_key = api_key
        parsed = urlparse(base_url)
        # If the URL is an HTTP(S) control plane, use HTTP client.
        # If the scheme is valkey:// but the native Python client isn't
        # installed, fall back to an HTTP control-plane interpretation so the
        # service can run against a Valkey container without the Python
        # dependency. Otherwise, if valkey is available and a valkey:// URL
        # is provided, use the native client for better performance.
        if parsed.scheme in ("http", "https") or (
            parsed.scheme == "valkey" and valkey is None
        ):
            self._mode = "http"
            # Convert valkey://host:port[/db] -> http://host:port for the
            # HTTP control plane fallback when necessary.
            if parsed.scheme == "valkey":
                host = parsed.hostname or "localhost"
                port = parsed.port or 6379
                self.base_url = f"http://{host}:{port}"
            else:
                self.base_url = base_url.rstrip("/")
            self.session = httpx.Client()
            if api_key:
                self.session.headers.update({"Authorization": f"Bearer {api_key}"})
        else:
            # native valkey client
            if valkey is None:
                raise RuntimeError("valkey client library not installed")
            self._mode = "client"
            # valkey://host:port/db or valkey://host:port
            host = parsed.hostname or "localhost"
            port = parsed.port or 6379
            db = 0
            if parsed.path and parsed.path.strip("/"):
                try:
                    db = int(parsed.path.strip("/"))
                except ValueError:
                    db = 0
            # decode_responses so we receive strings
            self.client = valkey.Valkey(
                host=host, port=port, db=db, decode_responses=True
            )

    def _url(self, path: str) -> str:
        return f"{self.base_url}{path}"

    def store_refresh_token(
        self, refresh_token: str, session_data: dict[str, Any], ttl_seconds: int
    ) -> None:
        if getattr(self, "_mode", "http") == "client":
            key = f"session:{refresh_token}"
            self.client.set(key, json.dumps(session_data))
            # set expire
            self.client.expire(key, ttl_seconds)
            return
        url = self._url("/sessions")
        body = {
            "refresh_token": refresh_token,
            "session": session_data,
            "ttl": ttl_seconds,
        }
        r = self.session.post(url, json=body, timeout=self.timeout)
        r.raise_for_status()

    def rotate_refresh_token(self, old_token: str, ttl_seconds: int) -> str | None:
        if getattr(self, "_mode", "http") == "client":
            old_key = f"session:{old_token}"
            val = self.client.get(old_key)
            if val is None:
                return None
            # create new token and atomically set new key then delete old key via pipeline
            new_token = uuid.uuid4().hex
            new_key = f"session:{new_token}"
            pipe = self.client.pipeline()
            pipe.set(new_key, val)
            pipe.expire(new_key, ttl_seconds)
            pipe.delete(old_key)
            pipe.execute()
            return new_token
        url = self._url("/sessions/rotate")
        body = {"old_token": old_token, "ttl": ttl_seconds}
        r = self.session.post(url, json=body, timeout=self.timeout)
        if r.status_code == 200:
            data = r.json()
            return data.get("new_token")
        if r.status_code == 404:
            return None
        r.raise_for_status()

    def revoke_refresh_token(self, refresh_token: str) -> None:
        if getattr(self, "_mode", "http") == "client":
            key = f"session:{refresh_token}"
            self.client.delete(key)
            return
        url = self._url("/sessions/revoke")
        body = {"token": refresh_token}
        r = self.session.post(url, json=body, timeout=self.timeout)
        r.raise_for_status()

    def is_refresh_revoked(self, refresh_token: str) -> bool:
        if getattr(self, "_mode", "http") == "client":
            key = f"session:{refresh_token}"
            val = self.client.get(key)
            return val is None
        url = self._url(f"/sessions/{refresh_token}")
        r = self.session.get(url, timeout=self.timeout)
        if r.status_code == 404:
            return True
        r.raise_for_status()
        return False

    def get_session(self, refresh_token: str) -> dict[str, Any] | None:
        if getattr(self, "_mode", "http") == "client":
            key = f"session:{refresh_token}"
            val = self.client.get(key)
            if val is None:
                return None
            try:
                return json.loads(val)
            except Exception:
                return None
        url = self._url(f"/sessions/{refresh_token}")
        r = self.session.get(url, timeout=self.timeout)
        if r.status_code == 404:
            return None
        r.raise_for_status()
        return r.json().get("session")


def get_session_store() -> SessionStore:
    """Factory: return ValkeySessionStore if VALKEY_URL configured, otherwise in-memory."""
    valkey_url = os.environ.get("VALKEY_URL")
    api_key = os.environ.get("VALKEY_API_KEY")
    if valkey_url:
        return ValkeySessionStore(valkey_url, api_key)
    return InMemorySessionStore()
