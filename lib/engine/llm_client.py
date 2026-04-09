"""Async LLM client for OpenRouter API."""

import json
import httpx
import logging
from functools import lru_cache
from typing import Any, Optional

from .config import get_settings

logger = logging.getLogger(__name__)


class LLMClient:
    """Async client for OpenRouter API."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        api_url: Optional[str] = None,
        model: Optional[str] = None,
    ):
        settings = get_settings()
        self.api_key = api_key or settings.openrouter_api_key
        self.api_url = api_url or settings.openrouter_api_url
        self.model = model or settings.openrouter_model
        self._client: Optional[httpx.AsyncClient] = None

    def _get_client(self) -> httpx.AsyncClient:
        """Return a reusable async HTTP client, creating one if needed."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(timeout=120.0)
        return self._client

    async def close(self) -> None:
        """Close the underlying HTTP client."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None

    async def generate(self, prompt: str, system_prompt: str) -> str:
        """
        Generate a response from the LLM.

        Args:
            prompt: The user prompt to send
            system_prompt: The system prompt defining the AI's role

        Returns:
            The generated response text

        Raises:
            httpx.HTTPError: If the API request fails
            ValueError: If the response format is unexpected
        """
        if not self.api_key:
            raise ValueError("OpenRouter API key not configured")

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/ai-agriculture-advisors",
        }

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt},
            ],
        }

        client = self._get_client()
        try:
            response = await client.post(
                self.api_url,
                headers=headers,
                json=payload,
            )
            response.raise_for_status()
            data = response.json()

            if "choices" not in data or not data["choices"]:
                raise ValueError("No choices in API response")

            return data["choices"][0]["message"]["content"]

        except httpx.HTTPStatusError as e:
            logger.error(f"OpenRouter API error: {e.response.status_code}")
            raise
        except httpx.RequestError as e:
            logger.error(f"Request error: {e}")
            raise
        except (KeyError, IndexError) as e:
            logger.error(f"Unexpected response format: {e}")
            raise ValueError(f"Unexpected API response format: {e}")

    async def generate_json(
        self,
        prompt: str,
        system_prompt: str,
        *,
        schema_name: str,
        schema: dict[str, Any],
        strict: bool = True,
    ) -> dict[str, Any]:
        """Generate a structured JSON response using a JSON schema."""
        if not self.api_key:
            raise ValueError("OpenRouter API key not configured")

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/ai-agriculture-advisors",
        }

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt},
            ],
            "response_format": {
                "type": "json_schema",
                "json_schema": {
                    "name": schema_name,
                    "strict": strict,
                    "schema": schema,
                },
            },
        }

        client = self._get_client()
        try:
            response = await client.post(
                self.api_url,
                headers=headers,
                json=payload,
            )
            response.raise_for_status()
            data = response.json()

            if "choices" not in data or not data["choices"]:
                raise ValueError("No choices in API response")

            content = data["choices"][0]["message"]["content"]
            if isinstance(content, dict):
                return content
            if isinstance(content, list):
                content = "".join(
                    item.get("text", "")
                    for item in content
                    if isinstance(item, dict)
                )
            if not isinstance(content, str) or not content.strip():
                raise ValueError("No JSON content in API response")
            parsed = json.loads(content)
            if not isinstance(parsed, dict):
                raise ValueError("Structured response was not a JSON object")
            return parsed

        except httpx.HTTPStatusError as e:
            logger.error(f"OpenRouter API error: {e.response.status_code}")
            raise
        except httpx.RequestError as e:
            logger.error(f"Request error: {e}")
            raise
        except (KeyError, IndexError, json.JSONDecodeError) as e:
            logger.error(f"Unexpected structured response format: {e}")
            raise ValueError(f"Unexpected structured API response format: {e}")


@lru_cache(maxsize=1)
def get_llm_client() -> LLMClient:
    """Return a cached LLM client instance."""
    return LLMClient()
