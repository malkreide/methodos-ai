"""litellm-backed LLMProvider — single class for all chat models."""

from __future__ import annotations

import litellm

from methodos.providers.base import LLMError


class LiteLLMProvider:
    """Wraps litellm.completion behind the LLMProvider Protocol.

    Construction:
        LiteLLMProvider(model="anthropic/claude-3-5-haiku-20241022")
        LiteLLMProvider(model="ollama/llama3.1:8b")
        LiteLLMProvider(model="openai/gpt-4o-mini")

    API keys are read from environment by litellm itself.

    `timeout` bounds each call. litellm's own default is 600 s, and the HTTP
    /query blocks on the explanation, so a stuck provider would hold back a
    finished ranking for ten minutes; a timeout instead raises LLMError, which
    the API reports as `explanation_error` with the ranking intact.
    """

    def __init__(self, model: str, timeout: float = 45.0) -> None:
        self.name = model
        self.timeout = timeout

    def complete(
        self,
        system: str,
        user: str,
        *,
        max_tokens: int = 1024,
        temperature: float = 0.2,
    ) -> str:
        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ]
        try:
            resp = litellm.completion(
                model=self.name,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
                timeout=self.timeout,
            )
        except Exception as e:
            raise LLMError(f"{type(e).__name__}: {e}") from e

        try:
            content = resp.choices[0].message.content
        except (AttributeError, IndexError, KeyError) as e:
            raise LLMError(f"unexpected response shape: {e}") from e
        if content is None:
            raise LLMError("litellm returned empty content")
        return str(content)
