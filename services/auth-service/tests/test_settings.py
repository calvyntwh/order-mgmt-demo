import os
import importlib


def test_validate_fails_on_insecure_secret(monkeypatch):
    monkeypatch.setenv("ENV", "production")
    monkeypatch.setenv("JWT_SECRET", "dev-secret")

    # reload settings module to pick up monkeypatched env
    settings = importlib.import_module("app.settings")
    importlib.reload(settings)

    try:
        settings.settings.validate()
        assert False, "validate() should raise SystemExit for insecure secret"
    except SystemExit:
        # expected
        pass
