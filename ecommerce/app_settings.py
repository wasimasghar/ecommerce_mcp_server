"""Loads all settings from .env so every file reads config from one place."""
from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=PROJECT_ROOT / ".env", extra="ignore")

    firebase_service_account_path: Path = Path("firebase-key.json")
    firebase_project_id: str
    firebase_web_api_key: str

    store_user_name: str = ""
    store_user_email: str
    store_user_password: str
    store_user_city: str = "Lahore"

    max_results: int = 10
    shipping_fee_pkr: int = 150
    free_shipping_above_pkr: int = 2000
    return_window_days: int = 7

    @property
    def service_account_file(self) -> Path:
        path = self.firebase_service_account_path
        return path if path.is_absolute() else PROJECT_ROOT / path


@lru_cache
def get_settings() -> Settings:
    return Settings()