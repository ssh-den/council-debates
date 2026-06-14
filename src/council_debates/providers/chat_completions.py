"""Client for OpenAI-compatible chat completion providers."""

from __future__ import annotations

import logging
import time
from typing import Any, Protocol

from council_debates.core.models import ProviderConfig

logger = logging.getLogger(__name__)


class LLMClientProtocol(Protocol):
    def complete(
        self,
        *,
        provider_name: str,
        model: str,
        system_prompt: str,
        user_prompt: str,
        temperature: float,
        max_tokens: int,
    ) -> str: ...


class LLMClientError(RuntimeError):
    """Raised when an API call fails or returns no text."""


class ChatCompletionsClient:
    """Thin client for OpenAI-compatible ``/v1/chat/completions`` providers."""

    def __init__(self, providers: dict[str, ProviderConfig]):
        self.providers = providers

    def _client_for(self, provider_name: str) -> Any:
        try:
            provider = self.providers[provider_name]
        except KeyError as exc:
            raise LLMClientError(f"Provider not found: {provider_name}") from exc
        if not provider.api_key:
            raise LLMClientError(f"Provider '{provider_name}' has no resolved API key.")
        try:
            from openai import OpenAI
        except ImportError as exc:
            raise LLMClientError(
                "The 'openai' package is required for API calls. "
                "Install dependencies with 'pip install .'"
            ) from exc
        return OpenAI(
            api_key=provider.api_key,
            base_url=provider.base_url,
            max_retries=3,
        )

    def complete(
        self,
        *,
        provider_name: str,
        model: str,
        system_prompt: str,
        user_prompt: str,
        temperature: float,
        max_tokens: int,
    ) -> str:
        logger.info("Calling provider=%s model=%s", provider_name, model)
        client = self._client_for(provider_name)
        last_exc: Exception | None = None
        for attempt in range(3):
            try:
                completion = client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
            except Exception as exc:
                last_exc = exc
                if attempt < 2:
                    time.sleep(0.2 * (attempt + 1))
                    continue
                break
            try:
                content = completion.choices[0].message.content
            except Exception as exc:
                raise LLMClientError(
                    "Malformed chat completion response for "
                    f"provider={provider_name!r}, model={model!r}."
                ) from exc
            if content is None or not str(content).strip():
                last_exc = LLMClientError(
                    "Empty chat completion response for "
                    f"provider={provider_name!r}, model={model!r}."
                )
                if attempt < 2:
                    time.sleep(0.2 * (attempt + 1))
                    continue
                break
            return str(content)
        raise LLMClientError(
            f"Chat completion failed for provider={provider_name!r}, model={model!r}: {last_exc}"
        ) from last_exc
