import os
from dataclasses import dataclass


@dataclass
class Settings:
    JWT_SECRET: str = os.getenv("JWT_SECRET", "dev-secret")
    ENV: str = os.getenv("ENV", "development")
    MIN_SECRET_LENGTH: int = int(os.getenv("MIN_SECRET_LENGTH", "16"))

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


settings = Settings()
