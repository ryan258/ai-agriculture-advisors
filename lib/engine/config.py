"""Configuration management for AI Advisors."""

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
    openrouter_synthesis_model: str = ""

    @staticmethod
    def _parse_bool(value: str) -> bool:
        return value.strip().lower() in {"1", "true", "yes", "y", "on"}

    @classmethod
    def from_env(cls) -> "Settings":
        """Load and validate settings from environment variables."""
        instance = cls(
            openrouter_api_key=os.getenv("OPENROUTER_API_KEY", ""),
            openrouter_api_url=os.getenv("OPENROUTER_API_URL", ""),
            openrouter_model=os.getenv("OPENROUTER_MODEL", ""),
            openrouter_synthesis_model=os.getenv(
                "OPENROUTER_SYNTHESIS_MODEL", ""
            ).strip(),
            port=int(os.getenv("PORT", "8123")),
            allow_missing_api_key=cls._parse_bool(
                os.getenv("ALLOW_MISSING_API_KEY", "false")
            ),
        )
        instance.validate()
        return instance

    def validate(self) -> None:
        """Validate required settings are present."""
        if not self.openrouter_api_key and not self.allow_missing_api_key:
            raise ValueError("OPENROUTER_API_KEY environment variable is required")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Load settings once on demand."""
    return Settings.from_env()
