"""Tests for the LLM client."""

import json
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


@respx.mock
@pytest.mark.asyncio
async def test_generate_json_success(client: LLMClient) -> None:
    """Test structured JSON generation."""
    route = respx.post("https://api.test.com/v1/chat/completions").mock(
        return_value=httpx.Response(
            200,
            json={
                "choices": [
                    {
                        "message": {
                            "content": '{"governing_insight":"Use irrigation discipline."}'
                        }
                    }
                ]
            },
        )
    )

    result = await client.generate_json(
        "Test prompt",
        "Test system prompt",
        schema_name="roundtable_consensus",
        schema={
            "type": "object",
            "properties": {"governing_insight": {"type": "string"}},
            "required": ["governing_insight"],
        },
    )

    payload = json.loads(route.calls[0].request.content)
    assert payload["response_format"]["type"] == "json_schema"
    assert payload["response_format"]["json_schema"]["name"] == "roundtable_consensus"
    assert result["governing_insight"] == "Use irrigation discipline."


@respx.mock
@pytest.mark.asyncio
async def test_generate_json_invalid_payload(client: LLMClient) -> None:
    """Test invalid structured payload handling."""
    respx.post("https://api.test.com/v1/chat/completions").mock(
        return_value=httpx.Response(
            200,
            json={"choices": [{"message": {"content": "not-json"}}]},
        )
    )

    with pytest.raises(ValueError, match="structured API response format"):
        await client.generate_json(
            "Test prompt",
            "Test system prompt",
            schema_name="roundtable_consensus",
            schema={"type": "object"},
        )


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


POOL_ERROR = {
    "error": {
        "code": 429,
        "message": "Provider returned error",
        "metadata": {
            "provider_name": "DekaLLM",
            "limit_source": "upstream_provider_shared_pool",
            "raw": "provider details that must not be displayed",
        },
    }
}


@respx.mock
@pytest.mark.asyncio
async def test_shared_pool_fails_over_once_to_same_model_json_mode():
    client = LLMClient(
        api_key="test",
        api_url="https://openrouter.ai/api/v1/chat/completions",
        model="original-model",
    )
    route = respx.post(client.api_url).mock(
        side_effect=[
            httpx.Response(429, json=POOL_ERROR),
            httpx.Response(
                200,
                json={"choices": [{"message": {"content": '{"answer":"Recovered"}'}}]},
            ),
        ]
    )
    schema = {"type": "object", "properties": {"answer": {"type": "string"}}}
    result = await client.generate_json(
        "Original prompt", "Original instructions", schema_name="test", schema=schema
    )
    assert result == {"answer": "Recovered"}
    assert route.call_count == 2
    original, fallback = [json.loads(call.request.content) for call in route.calls]
    assert original["response_format"]["type"] == "json_schema"
    assert fallback["model"] == original["model"] == "original-model"
    assert fallback["response_format"] == {"type": "json_object"}
    assert fallback["provider"] == {
        "ignore": ["dekallm"],
        "allow_fallbacks": True,
        "require_parameters": True,
    }
    assert fallback["messages"][1] == original["messages"][1]
    assert fallback["messages"][0]["content"].startswith("Original instructions")
    assert json.dumps(schema) in fallback["messages"][0]["content"]
    await client.close()


@respx.mock
@pytest.mark.asyncio
@pytest.mark.parametrize(
    "source", [None, "openrouter_in_flight_budget", "openrouter_key_limit"]
)
async def test_other_limits_do_not_trigger_provider_failover(source):
    client = LLMClient(
        api_key="test",
        api_url="https://openrouter.ai/api/v1/chat/completions",
        model="original-model",
    )
    route = respx.post(client.api_url).mock(
        return_value=httpx.Response(
            429,
            json={
                "error": {
                    "metadata": {"provider_name": "DekaLLM", "limit_source": source}
                }
            },
        )
    )
    with pytest.raises(httpx.HTTPStatusError):
        await client.generate_json("Prompt", "System", schema_name="test", schema={})
    assert route.call_count == 1
    await client.close()


@respx.mock
@pytest.mark.asyncio
async def test_shared_pool_failover_is_bounded_and_keeps_last_error():
    client = LLMClient(
        api_key="test",
        api_url="https://openrouter.ai/api/v1/chat/completions",
        model="original-model",
    )
    route = respx.post(client.api_url).mock(
        return_value=httpx.Response(
            429, json=POOL_ERROR, headers={"Retry-After": "120"}
        )
    )
    with pytest.raises(httpx.HTTPStatusError) as caught:
        await client.generate_json("Prompt", "System", schema_name="test", schema={})
    assert route.call_count == 2
    assert caught.value.response.headers["Retry-After"] == "120"
    await client.close()


@respx.mock
@pytest.mark.asyncio
async def test_upstream_error_in_success_envelope_remains_rate_limit(client):
    respx.post(client.api_url).mock(return_value=httpx.Response(200, json=POOL_ERROR))
    with pytest.raises(httpx.HTTPStatusError) as caught:
        await client.generate_json("Prompt", "System", schema_name="test", schema={})
    assert caught.value.response.status_code == 429
    assert caught.value.response.json() == POOL_ERROR
