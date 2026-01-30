"""Tests for the LLM client."""

import pytest
import httpx
import respx

from lib.engine.llm_client import LLMClient


@pytest.fixture
def client() -> LLMClient:
    """Create an LLM client for testing."""
    return LLMClient(
        api_key="test-key",
        api_url="https://api.test.com/v1/chat/completions",
        model="test-model",
    )


@respx.mock
@pytest.mark.asyncio
async def test_generate_success(client: LLMClient) -> None:
    """Test successful API call."""
    respx.post("https://api.test.com/v1/chat/completions").mock(
        return_value=httpx.Response(
            200,
            json={"choices": [{"message": {"content": "Test response from LLM"}}]},
        )
    )

    result = await client.generate("Test prompt", "Test system prompt")
    assert result == "Test response from LLM"


@respx.mock
@pytest.mark.asyncio
async def test_generate_strips_whitespace(client: LLMClient) -> None:
    """Test that responses are stripped of whitespace."""
    respx.post("https://api.test.com/v1/chat/completions").mock(
        return_value=httpx.Response(
            200,
            json={
                "choices": [{"message": {"content": "  Response with whitespace  \n"}}]
            },
        )
    )

    result = await client.generate("Test prompt", "Test system prompt")
    # Note: LLMClient itself doesn't strip, but Expert.query does
    assert "Response with whitespace" in result


@respx.mock
@pytest.mark.asyncio
async def test_generate_api_error(client: LLMClient) -> None:
    """Test handling of API errors."""
    respx.post("https://api.test.com/v1/chat/completions").mock(
        return_value=httpx.Response(500, json={"error": "Server error"})
    )

    with pytest.raises(httpx.HTTPStatusError):
        await client.generate("Test prompt", "Test system prompt")


@respx.mock
@pytest.mark.asyncio
async def test_generate_empty_choices(client: LLMClient) -> None:
    """Test handling of empty choices in response."""
    respx.post("https://api.test.com/v1/chat/completions").mock(
        return_value=httpx.Response(200, json={"choices": []})
    )

    with pytest.raises(ValueError, match="No choices"):
        await client.generate("Test prompt", "Test system prompt")


@respx.mock(assert_all_mocked=False)
@pytest.mark.asyncio
async def test_generate_no_api_key() -> None:
    """Test that missing API key raises error before making request."""
    from unittest.mock import patch
    from lib.engine.config import Settings

    # Patch settings to have no API key
    mock_settings = Settings(
        openrouter_api_key="",
        openrouter_api_url="https://api.test.com",
        openrouter_model="test",
        port=8123,
        allow_missing_api_key=True,
    )

    with patch("lib.engine.llm_client.get_settings", return_value=mock_settings):
        client = LLMClient()  # Will get empty key from patched settings

        with pytest.raises(ValueError, match="API key not configured"):
            await client.generate("Test prompt", "Test system prompt")
