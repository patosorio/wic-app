"""Application settings loaded from environment variables."""

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application configuration loaded from environment variables.
    Reads from .env file in the backend root when present.
    """

    model_config = SettingsConfigDict(
        env_file=str(Path(__file__).resolve().parent.parent / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    database_url: str
    dev_bypass_auth: bool = False
    dev_skip_firestore: bool = False
    dev_skip_stripe: bool = False
    firebase_project_id: str
    firebase_service_account_key_path: str | None = None
    stripe_secret_key: str | None = None
    stripe_webhook_secret: str | None = None
    gcp_project_id: str
    gcs_bucket: str = "wic-releases"
    service_b_internal_url: str


def get_settings() -> Settings:
    """Return the application settings singleton."""
    return Settings()


settings = get_settings()
