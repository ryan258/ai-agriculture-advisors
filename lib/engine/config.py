"""Configuration management for AI Advisors."""

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from urllib.parse import urlsplit
from dotenv import load_dotenv
from lib.contracts import MODEL_ID

PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(PROJECT_ROOT / ".env")


def validate_provider(api_url: str, model: str) -> None:
    if not MODEL_ID.fullmatch(model) or model == "your_model_id_here":
        raise ValueError("Set OPENROUTER_MODEL to an available provider model ID")
    try:
        url = urlsplit(api_url)
        valid_port = url.port
    except ValueError:
        raise ValueError("Set OPENROUTER_API_URL to a valid provider URL") from None
    if (
        url.scheme not in ("https", "http")
        or not url.hostname
        or url.username
        or url.password
        or url.fragment
    ):
        raise ValueError(
            "Set OPENROUTER_API_URL to a valid provider URL without embedded credentials or fragments"
        )
    if valid_port is not None and not 1 <= valid_port <= 65535:
        raise ValueError("Provider URL port must be between 1 and 65535")
    if url.scheme == "http" and url.hostname not in ("localhost", "127.0.0.1", "::1"):
        raise ValueError("Remote provider URLs must use HTTPS")


@dataclass
class Settings:
    """Application settings loaded from environment variables."""

    openrouter_api_key: str
    openrouter_api_url: str
    openrouter_model: str
    port: int
    allow_missing_api_key: bool
    openrouter_synthesis_model: str = ""
    max_output_tokens: int = 1800
    max_run_calls: int = 32
    max_run_seconds: int = 600
    max_prompt_chars: int = 120000
    max_run_attempts: int = 3

    @staticmethod
    def _parse_bool(value: str) -> bool:
        return value.strip().lower() in {"1", "true", "yes", "y", "on"}

    @staticmethod
    def _integer(name: str, default: str) -> int:
        try:
            return int(os.getenv(name, default))
        except ValueError:
            raise ValueError(f"{name} must be an integer") from None

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
            port=cls._integer("PORT", "8123"),
            allow_missing_api_key=cls._parse_bool(
                os.getenv("ALLOW_MISSING_API_KEY", "false")
            ),
            max_output_tokens=cls._integer("MAX_OUTPUT_TOKENS", "1800"),
            max_run_calls=cls._integer("MAX_RUN_CALLS", "32"),
            max_run_seconds=cls._integer("MAX_RUN_SECONDS", "600"),
            max_prompt_chars=cls._integer("MAX_PROMPT_CHARS", "120000"),
            max_run_attempts=cls._integer("MAX_RUN_ATTEMPTS", "3"),
        )
        instance.validate()
        return instance

    def validate(self) -> None:
        """Validate required settings are present."""
        if not self.openrouter_api_key.strip() and not self.allow_missing_api_key:
            raise ValueError("OPENROUTER_API_KEY environment variable is required")
        if not 1 <= self.port <= 65535:
            raise ValueError("PORT must be between 1 and 65535")
        for name, value, minimum, maximum in (
            ("MAX_OUTPUT_TOKENS", self.max_output_tokens, 64, 16000),
            ("MAX_RUN_CALLS", self.max_run_calls, 3, 100),
            ("MAX_RUN_SECONDS", self.max_run_seconds, 30, 3600),
            ("MAX_PROMPT_CHARS", self.max_prompt_chars, 1000, 500000),
            ("MAX_RUN_ATTEMPTS", self.max_run_attempts, 1, 10),
        ):
            if not minimum <= value <= maximum:
                raise ValueError(f"{name} must be between {minimum} and {maximum}")
        if not self.allow_missing_api_key:
            if self.openrouter_api_key.strip() == "your_api_key_here":
                raise ValueError("Replace the OPENROUTER_API_KEY placeholder in .env")
            validate_provider(self.openrouter_api_url, self.openrouter_model)
            if self.openrouter_synthesis_model:
                validate_provider(
                    self.openrouter_api_url, self.openrouter_synthesis_model
                )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Load settings once on demand."""
    return Settings.from_env()
