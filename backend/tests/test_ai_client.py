import httpx
import openai
import pytest

from app.services import ai_client
from app.services.ai_client import AIError, chat

MESSAGES = [{"role": "user", "content": "안녕"}]


def use_handler(monkeypatch, handler):
    client = openai.OpenAI(
        base_url="http://ai.test/v1",
        api_key="test",
        max_retries=0,
        http_client=httpx.Client(transport=httpx.MockTransport(handler)),
    )
    monkeypatch.setattr(ai_client, "get_client", lambda: client)


def test_chat_success(monkeypatch):
    def handler(request):
        return httpx.Response(
            200,
            json={
                "id": "c1",
                "object": "chat.completion",
                "created": 0,
                "model": "gpt-5-mini",
                "choices": [
                    {
                        "index": 0,
                        "message": {"role": "assistant", "content": "반갑습니다"},
                        "finish_reason": "stop",
                    }
                ],
                "usage": {"prompt_tokens": 12, "completion_tokens": 5, "total_tokens": 17},
            },
        )

    use_handler(monkeypatch, handler)
    result = chat("gpt-5-mini", MESSAGES, 100)

    assert result.content == "반갑습니다"
    assert result.input_tokens == 12
    assert result.output_tokens == 5


def test_chat_timeout(monkeypatch):
    def handler(request):
        raise httpx.ReadTimeout("timeout", request=request)

    use_handler(monkeypatch, handler)
    with pytest.raises(AIError) as e:
        chat("gpt-5-mini", MESSAGES, 100)
    assert e.value.code == "AI_TIMEOUT"


@pytest.mark.parametrize(
    "response",
    [
        httpx.Response(500, json={"error": {"message": "server error"}}),
        httpx.Response(
            200,
            json={
                "id": "c1",
                "object": "chat.completion",
                "created": 0,
                "model": "gpt-5-mini",
                "choices": [
                    {
                        "index": 0,
                        "message": {"role": "assistant", "content": ""},
                        "finish_reason": "stop",
                    }
                ],
            },
        ),
    ],
)
def test_chat_error(monkeypatch, response):
    use_handler(monkeypatch, lambda request: response)
    with pytest.raises(AIError) as e:
        chat("gpt-5-mini", MESSAGES, 100)
    assert e.value.code == "AI_ERROR"


def test_chat_connection_error(monkeypatch):
    def handler(request):
        raise httpx.ConnectError("refused", request=request)

    use_handler(monkeypatch, handler)
    with pytest.raises(AIError) as e:
        chat("gpt-5-mini", MESSAGES, 100)
    assert e.value.code == "AI_ERROR"
