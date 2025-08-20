import os


def test_validate_fails_with_default_dev_secret(monkeypatch):
    monkeypatch.setenv("ENV", "production")
    # ensure default dev-secret is present
    monkeypatch.setenv("JWT_SECRET", "dev-secret")
    monkeypatch.setenv("BCRYPT_ROUNDS", "12")
    # import settings module from local app package
    import importlib, sys

    sys.path.insert(0, "services/auth-service")
    try:
        # ensure a fresh import so the Settings dataclass picks up current env
        sys.modules.pop("app.settings", None)
        sys.modules.pop("app", None)
        mod = importlib.import_module("app.settings")
        try:
            mod.settings.validate()
            raise AssertionError("validate() should have exited for invalid secret")
        except SystemExit:
            # expected
            pass
    finally:
        # cleanup path
        try:
            sys.path.remove("services/auth-service")
        except ValueError:
            pass


def test_validate_passes_with_strong_values(monkeypatch):
    monkeypatch.setenv("ENV", "production")
    monkeypatch.setenv("JWT_SECRET", "x" * 40)
    monkeypatch.setenv("BCRYPT_ROUNDS", "12")
    import importlib, sys

    sys.path.insert(0, "services/auth-service")
    try:
        sys.modules.pop("app.settings", None)
        sys.modules.pop("app", None)
        mod = importlib.import_module("app.settings")
        # Should not raise
        mod.settings.validate()
    finally:
        try:
            sys.path.remove("services/auth-service")
        except ValueError:
            pass
