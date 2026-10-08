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

    Two things differ between the models this has to serve, and both broke the
    Docker default (`anthropic/claude-opus-5`) before anyone noticed, because no
    test ever reached a live Anthropic model:

      * Current Claude models reject `temperature` (and other sampling
        parameters); litellm refuses the call before sending it. `drop_params`
        drops what a model does not take, so the same call works on Claude,
        Ollama and OpenAI alike — for models that still accept it, the
        temperature is sent as before.
      * Current Claude models think before answering, and the thinking counts
        against `max_tokens`. A budget sized for the visible answer alone can be
        used up before the answer starts; that surfaces as an empty reply with
        finish_reason "length", reported below in words a person can act on.
    """

    def __init__(self, model: str) -> None:
        self.name = model

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
                drop_params=True,
            )
        except Exception as e:
            raise LLMError(f"{type(e).__name__}: {e}") from e

        try:
            choice = resp.choices[0]
            content = choice.message.content
        except (AttributeError, IndexError, KeyError) as e:
            raise LLMError(f"unexpected response shape: {e}") from e
        if not content:
            if getattr(choice, "finish_reason", None) == "length":
                raise LLMError(
                    f"{self.name} stopped at max_tokens={max_tokens} before writing an "
                    "answer — a model that thinks first counts its thinking against "
                    "that limit"
                )
            raise LLMError("litellm returned empty content")
        return str(content)
