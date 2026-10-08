"""litellm-backed LLMProvider — single class for all chat models."""

from __future__ import annotations

import os

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

    A key that is not a key is caught before the call, too: the key travels in
    an HTTP header, and a placeholder copied from the docs (`sk-ant-api03-…`)
    otherwise surfaces as litellm's "'ascii' codec can't encode character",
    which names neither the key nor the file it came from.
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
        problem = key_problem(self.name)
        if problem:
            raise LLMError(problem)
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


def key_problem(model: str, environ: dict[str, str] | None = None) -> str | None:
    """Why the API key for `model` cannot work, or None if nothing is visibly wrong.

    Looks only at the variable litellm reads for the model's provider
    (`anthropic/...` → ANTHROPIC_API_KEY). A missing key is left to litellm,
    which already says so; a local model such as `ollama/...` has none. The
    message never contains the key, only what is wrong with it.
    """
    env = os.environ if environ is None else environ
    provider, sep, _ = model.partition("/")
    if not sep:
        return None
    var = f"{provider.upper()}_API_KEY"
    key = env.get(var)
    if not key:
        return None
    for i, ch in enumerate(key):
        if not ch.isascii() or ch.isspace():
            return (
                f"{var} contains {ch!r} at position {i}; an API key is plain ASCII "
                "without spaces. Paste the whole key again (a placeholder such as "
                "'sk-ant-api03-…' from the docs is not one), in .env or wherever it is set."
            )
    if "..." in key or key.startswith("<"):
        return (
            f"{var} looks like a placeholder, not a key. Paste the whole key, "
            "in .env or wherever it is set."
        )
    return None
