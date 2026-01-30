"""Configuration management for AI Agriculture Advisors."""

import os
from dataclasses import dataclass
from functools import lru_cache
from dotenv import load_dotenv

load_dotenv()


@dataclass
class Settings:
    """Application settings loaded from environment variables."""

    openrouter_api_key: str
    openrouter_api_url: str
    openrouter_model: str
    port: int
    allow_missing_api_key: bool

    @staticmethod
    def _parse_bool(value: str) -> bool:
        return value.strip().lower() in {"1", "true", "yes", "y", "on"}

    @classmethod
    def from_env(cls) -> "Settings":
        """Load settings from environment variables."""
        return cls(
            openrouter_api_key=os.getenv("OPENROUTER_API_KEY", ""),
            openrouter_api_url=os.getenv(
                "OPENROUTER_API_URL",
                "https://openrouter.ai/api/v1/chat/completions",
            ),
            openrouter_model=os.getenv(
                "OPENROUTER_MODEL", "mistralai/mistral-7b-instruct:free"
            ),
            port=int(os.getenv("PORT", "8123")),
            allow_missing_api_key=cls._parse_bool(
                os.getenv("ALLOW_MISSING_API_KEY", "false")
            ),
        )

    def validate(self) -> None:
        """Validate required settings are present."""
        if not self.openrouter_api_key and not self.allow_missing_api_key:
            raise ValueError("OPENROUTER_API_KEY environment variable is required")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Load settings once on demand."""
    return Settings.from_env()
