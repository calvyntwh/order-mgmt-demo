import os
from dataclasses import dataclass


@dataclass
class Settings:
    JWT_SECRET: str = os.getenv("JWT_SECRET", "dev-secret")
    ENV: str = os.getenv("ENV", "development")
    MIN_SECRET_LENGTH: int = int(os.getenv("MIN_SECRET_LENGTH", "16"))
    # bcrypt work factor (cost). Keep a low default for fast local dev cycles,
    # but enforce a stronger minimum when not running in development.
    # Recommended production value: >= 12
    BCRYPT_ROUNDS: int = int(os.getenv("BCRYPT_ROUNDS", "4"))
    # Expected JWT signing algorithm (only allow strong symmetric algos here)
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    # Minimum bcrypt rounds to require when ENV != development
    MIN_BCRYPT_ROUNDS: int = int(os.getenv("MIN_BCRYPT_ROUNDS", "12"))

    def validate(self) -> None:
        """Fail-fast validation for critical runtime settings.

        Raises SystemExit when running outside development with insecure/missing secret.
        """
        if self.ENV != "development":
            secret = (self.JWT_SECRET or "").strip()
            if (
                not secret
                or secret == "dev-secret"
                or len(secret) < self.MIN_SECRET_LENGTH
            ):
                raise SystemExit("Invalid JWT_SECRET for non-development environment")
            # enforce bcrypt work factor in non-development envs
            if getattr(self, "BCRYPT_ROUNDS", 0) < getattr(
                self, "MIN_BCRYPT_ROUNDS", 12
            ):
                raise SystemExit(
                    f"BCRYPT_ROUNDS too low for non-development environment (got={self.BCRYPT_ROUNDS}, want>={self.MIN_BCRYPT_ROUNDS})"
                )
            # enforce allowed JWT algorithms (avoid `none` or weak choices)
            allowed = {"HS256", "HS512"}
            if (self.JWT_ALGORITHM or "").upper() not in allowed:
                raise SystemExit(
                    f"JWT_ALGORITHM must be one of {sorted(allowed)} in non-development environments"
                )


settings = Settings()
