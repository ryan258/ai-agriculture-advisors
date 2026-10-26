"""Async LLM client for OpenRouter API."""

import json
import httpx
import logging
import re
import time
from datetime import datetime, timezone
from urllib.parse import urlsplit
from functools import lru_cache
from typing import Any, Optional

from .config import get_settings, validate_provider
from .execution import current_execution
from lib.contracts import fingerprint, validate_schema

logger = logging.getLogger(__name__)


class LLMClient:
    """Async client for OpenRouter API."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        api_url: Optional[str] = None,
        model: Optional[str] = None,
    ) -> None:
        settings = get_settings()
        self.api_key = api_key or settings.openrouter_api_key
        self.api_url = api_url or settings.openrouter_api_url
        self.model = model or settings.openrouter_model
        self._client: Optional[httpx.AsyncClient] = None

    async def _post(
        self, headers: dict[str, str], payload: dict[str, Any]
    ) -> httpx.Response:
        settings = get_settings()
        if not self.api_url or not payload.get("model"):
            raise ValueError(
                "Configure a provider URL and model before sending a request"
            )
        validate_provider(self.api_url, payload["model"])
        if (
            sum(len(str(item.get("content", ""))) for item in payload["messages"])
            > settings.max_prompt_chars
        ):
            raise ValueError(
                "The supplied context exceeds this installation's prompt limit. Use a smaller excerpt or fewer turns."
            )
        payload["max_tokens"] = settings.max_output_tokens
        execution = current_execution.get()
        receipt: dict[str, Any] = {
            "configured_model": payload["model"],
            "request_sha256": fingerprint(payload),
            "started_at": datetime.now(timezone.utc).isoformat(),
            "status": "in_flight",
            "rule_version": "advisors-3",
            "max_output_tokens": settings.max_output_tokens,
        }
        if execution:
            execution.before_call()
            execution.receipts.append(receipt)
            # Persist the in-flight marker before dispatch. A crash here is ambiguous.
            await execution.checkpoint()
        started = time.monotonic()
        try:
            timeout = (
                min(
                    120.0,
                    max(
                        0.1, execution.timeout - (time.monotonic() - execution.started)
                    ),
                )
                if execution
                else 120.0
            )
            response = await self._get_client().post(
                self.api_url, headers=headers, json=payload, timeout=timeout
            )
            receipt["http_status"] = response.status_code
            receipt["status"] = "returned"
            try:
                data = response.json()
                if isinstance(data, dict):
                    receipt.update(
                        {
                            key: data[key]
                            for key in ("id", "model", "provider", "usage")
                            if key in data
                        }
                    )
                    choices = data.get("choices")
                    if (
                        isinstance(choices, list)
                        and choices
                        and isinstance(choices[0], dict)
                    ):
                        receipt["finish_reason"] = choices[0].get(
                            "finish_reason", "unknown"
                        )
            except ValueError:
                receipt["status"] = "invalid_json"
            return response
        except httpx.HTTPError:
            # A transport timeout/reset cannot tell us whether the provider
            # received or completed the request. Recovery must be deliberate.
            receipt["status"] = "transport_uncertain"
            raise
        finally:
            receipt["elapsed_seconds"] = round(time.monotonic() - started, 3)
            receipt["ended_at"] = datetime.now(timezone.utc).isoformat()
            if execution:
                await execution.checkpoint()

    @staticmethod
    def _response_data(response: httpx.Response) -> dict[str, Any]:
        response.raise_for_status()
        data = response.json()
        if not isinstance(data, dict):
            raise ValueError("Provider response was not an object")
        if isinstance(data.get("error"), dict):
            code = data["error"].get("code")
            status = code if type(code) is int and 400 <= code <= 599 else 502
            httpx.Response(
                status, headers=response.headers, json=data, request=response.request
            ).raise_for_status()
        return data

    @staticmethod
    def _content(data: dict[str, Any], *, structured: bool = False) -> Any:
        choices = data.get("choices")
        if (
            not isinstance(choices, list)
            or not choices
            or not isinstance(choices[0], dict)
        ):
            raise ValueError("No choices in API response")
        choice = choices[0]
        if choice.get("finish_reason") in (
            "length",
            "max_tokens",
            "content_filter",
            "error",
        ):
            raise ValueError(
                "Provider output was truncated or withheld; this is not a completed answer"
            )
        message = choice.get("message")
        if not isinstance(message, dict):
            raise ValueError("Provider omitted its message")
        content = message.get("content")
        if structured and isinstance(content, dict):
            return content
        if isinstance(content, list):
            if any(
                not isinstance(item, dict)
                or item.get("type", "text") != "text"
                or not isinstance(item.get("text"), str)
                for item in content
            ):
                raise ValueError("Unsupported provider content blocks")
            content = "".join(item["text"] for item in content)
        if not isinstance(content, str) or not content.strip():
            raise ValueError("Provider returned no usable text")
        return content

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

    async def generate(
        self, prompt: str, system_prompt: str, *, model: Optional[str] = None
    ) -> str:
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
        if not self.api_key.strip():
            raise ValueError("OpenRouter API key not configured")

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "http://localhost:8123",
        }

        execution = current_execution.get()
        payload: dict[str, Any] = {
            "model": model
            or (execution.advisor_model if execution else "")
            or self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt},
            ],
        }

        try:
            response = await self._post(headers, payload)
            return str(self._content(self._response_data(response)))

        except httpx.HTTPStatusError as e:
            logger.error(f"OpenRouter API error: {e.response.status_code}")
            raise
        except httpx.RequestError as e:
            logger.error("Provider connection failed (%s)", type(e).__name__)
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
        model: Optional[str] = None,
    ) -> dict[str, Any]:
        """Generate structured JSON, optionally using a task-specific model."""
        if not self.api_key.strip():
            raise ValueError("OpenRouter API key not configured")

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "http://localhost:8123",
        }

        payload: dict[str, Any] = {
            "model": model or self.model,
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

        try:
            response = await self._post(headers, payload)
            # Strict schemas can leave only one eligible upstream provider. A
            # confirmed shared-pool 429 permits ONE same-model JSON-mode attempt
            # through another provider; account/key limits must never trigger it.
            metadata = provider_error_metadata(response)
            provider_name = metadata.get("provider_name", "")
            if (
                response.status_code == 429
                and urlsplit(self.api_url).hostname == "openrouter.ai"
                and metadata.get("limit_source") == "upstream_provider_shared_pool"
                and isinstance(provider_name, str)
                and re.fullmatch(r"[A-Za-z0-9_-]{1,64}", provider_name)
            ):
                logger.warning(
                    "Structured provider shared pool exhausted; trying same-model JSON mode"
                )
                payload["provider"] = {
                    "ignore": [provider_name.lower()],
                    "allow_fallbacks": True,
                    "require_parameters": True,
                }
                payload["response_format"] = {"type": "json_object"}
                payload["messages"] = [
                    {
                        "role": "system",
                        "content": system_prompt
                        + "\nReturn only a JSON object conforming to this schema:\n"
                        + json.dumps(schema),
                    },
                    {"role": "user", "content": prompt},
                ]
                response = await self._post(headers, payload)
            data = self._response_data(response)
            content = self._content(data, structured=True)
            if isinstance(content, dict):
                validate_schema(content, schema)
                return content
            if isinstance(content, list):
                content = "".join(
                    item.get("text", "") for item in content if isinstance(item, dict)
                )
            if not isinstance(content, str) or not content.strip():
                raise ValueError("No JSON content in API response")
            parsed = json.loads(content)
            if not isinstance(parsed, dict):
                raise ValueError("Structured response was not a JSON object")
            validate_schema(parsed, schema)
            return parsed

        except httpx.HTTPStatusError as e:
            logger.error(f"OpenRouter API error: {e.response.status_code}")
            raise
        except httpx.RequestError as e:
            logger.error("Provider connection failed (%s)", type(e).__name__)
            raise
        except (KeyError, IndexError, json.JSONDecodeError) as e:
            logger.error(f"Unexpected structured response format: {e}")
            raise ValueError(f"Unexpected structured API response format: {e}")


@lru_cache(maxsize=1)
def get_llm_client() -> LLMClient:
    """Return a cached LLM client instance."""
    return LLMClient()


def provider_error_metadata(response: httpx.Response) -> dict[str, Any]:
    """Read structured error metadata without exposing raw provider payloads."""
    try:
        data = response.json()
    except ValueError:
        return {}
    error = data.get("error") if isinstance(data, dict) else None
    metadata = error.get("metadata") if isinstance(error, dict) else None
    return metadata if isinstance(metadata, dict) else {}
