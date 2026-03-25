"""最小 API 测试：使用 httpx.AsyncClient + ASGITransport 和 mock 验证各场景"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.main import app

BASE_URL = "http://test"
ENDPOINT = "/v1/capabilities/run"

MOCK_SUMMARY = "This is a mocked summary of the text."
MOCK_SENTIMENT_JSON = '{"sentiment": "positive", "confidence": 0.95, "reason": "The text expresses joy."}'


def _make_mock_http_response(content: str, status_code: int = 200) -> MagicMock:
    """构造一个模拟的 httpx Response 对象"""
    mock_resp = MagicMock()
    mock_resp.status_code = status_code
    mock_resp.json.return_value = {
        "choices": [{"message": {"content": content}}]
    }
    return mock_resp


@pytest_asyncio.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url=BASE_URL) as ac:
        yield ac


@pytest.mark.asyncio
async def test_text_summary_success(client: AsyncClient):
    """text_summary 正常调用应返回 ok=true 和 result 字段"""
    mock_http_resp = _make_mock_http_response(MOCK_SUMMARY)

    with patch("app.capabilities.text_summary.httpx.AsyncClient") as MockClient:
        instance = AsyncMock()
        instance.__aenter__ = AsyncMock(return_value=instance)
        instance.__aexit__ = AsyncMock(return_value=False)
        instance.post = AsyncMock(return_value=mock_http_resp)
        MockClient.return_value = instance

        resp = await client.post(
            ENDPOINT,
            json={
                "capability": "text_summary",
                "input": {"text": "Long text content for summarization.", "max_length": 50},
                "request_id": "test-001",
            },
        )

    assert resp.status_code == 200
    body = resp.json()
    assert body["ok"] is True
    assert "result" in body["data"]
    assert body["meta"]["capability"] == "text_summary"
    assert body["meta"]["request_id"] == "test-001"
    assert isinstance(body["meta"]["elapsed_ms"], int)


@pytest.mark.asyncio
async def test_sentiment_analysis_success(client: AsyncClient):
    """sentiment_analysis 正常调用应返回 sentiment/confidence/reason"""
    mock_http_resp = _make_mock_http_response(MOCK_SENTIMENT_JSON)

    with patch("app.capabilities.sentiment_analysis.httpx.AsyncClient") as MockClient:
        instance = AsyncMock()
        instance.__aenter__ = AsyncMock(return_value=instance)
        instance.__aexit__ = AsyncMock(return_value=False)
        instance.post = AsyncMock(return_value=mock_http_resp)
        MockClient.return_value = instance

        resp = await client.post(
            ENDPOINT,
            json={
                "capability": "sentiment_analysis",
                "input": {"text": "I love this product! It's amazing."},
                "request_id": "test-002",
            },
        )

    assert resp.status_code == 200
    body = resp.json()
    assert body["ok"] is True
    result = body["data"]["result"]
    assert result["sentiment"] in ("positive", "negative", "neutral")
    assert 0.0 <= result["confidence"] <= 1.0
    assert body["meta"]["capability"] == "sentiment_analysis"


@pytest.mark.asyncio
async def test_capability_not_found(client: AsyncClient):
    """未知 capability 应返回 CAPABILITY_NOT_FOUND 错误，且带 meta 字段"""
    resp = await client.post(
        ENDPOINT,
        json={"capability": "unknown_capability", "input": {}},
    )
    assert resp.status_code == 404
    body = resp.json()
    assert body["ok"] is False
    assert body["error"]["code"] == "CAPABILITY_NOT_FOUND"
    assert body["meta"]["capability"] == "unknown_capability"


@pytest.mark.asyncio
async def test_invalid_input_missing_text(client: AsyncClient):
    """text_summary 缺少 text 字段，应返回 INVALID_INPUT 错误"""
    resp = await client.post(
        ENDPOINT,
        json={"capability": "text_summary", "input": {"max_length": 100}},
    )
    assert resp.status_code == 422
    body = resp.json()
    assert body["ok"] is False
    assert body["error"]["code"] == "INVALID_INPUT"


@pytest.mark.asyncio
async def test_request_id_auto_generated(client: AsyncClient):
    """不传 request_id 时，应自动生成非空字符串"""
    mock_http_resp = _make_mock_http_response(MOCK_SUMMARY)

    with patch("app.capabilities.text_summary.httpx.AsyncClient") as MockClient:
        instance = AsyncMock()
        instance.__aenter__ = AsyncMock(return_value=instance)
        instance.__aexit__ = AsyncMock(return_value=False)
        instance.post = AsyncMock(return_value=mock_http_resp)
        MockClient.return_value = instance

        resp = await client.post(
            ENDPOINT,
            json={"capability": "text_summary", "input": {"text": "Test text."}},
        )

    assert resp.status_code == 200
    body = resp.json()
    assert body["ok"] is True
    assert body["meta"]["request_id"] != ""
