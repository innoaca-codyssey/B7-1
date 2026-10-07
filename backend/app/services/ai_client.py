from dataclasses import dataclass
from functools import cache

import openai

from app.config import settings


@dataclass
class AIResult:
    content: str
    input_tokens: int
    output_tokens: int


class AIError(Exception):
    def __init__(self, code: str):
        super().__init__(code)
        self.code = code


@cache
def get_client() -> openai.OpenAI:
    return openai.OpenAI(
        base_url=settings.ai_base_url,
        api_key=settings.ai_api_key,
        timeout=settings.ai_timeout_seconds,
        max_retries=0,
    )


def chat(model: str, messages: list[dict], max_tokens: int) -> AIResult:
    try:
        response = get_client().chat.completions.create(
            model=model, messages=messages, max_tokens=max_tokens
        )
    except openai.APITimeoutError as e:
        raise AIError("AI_TIMEOUT") from e
    except openai.OpenAIError as e:
        raise AIError("AI_ERROR") from e

    content = response.choices[0].message.content if response.choices else None
    if not content or not content.strip():
        raise AIError("AI_ERROR")

    usage = response.usage
    return AIResult(
        content=content,
        input_tokens=usage.prompt_tokens if usage else 0,
        output_tokens=usage.completion_tokens if usage else 0,
    )
