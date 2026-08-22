"""
Multi-provider LLM Service: Supports OpenAI, Anthropic, and Ollama.
Provides chat completion, embeddings, and structured output generation.
Falls back gracefully when no LLM is configured.
"""

from __future__ import annotations

import json
import hashlib
import socket
import time
from typing import Any
from urllib.parse import urlparse

import structlog

from backend.app.core.config import settings

log = structlog.get_logger()

_OLLAMA_PROBE_TTL_SECONDS = 30.0

_openai_client = None
_anthropic_client = None


def _get_openai_client():
    global _openai_client
    if _openai_client is None and settings.openai_api_key:
        try:
            from openai import AsyncOpenAI
            _openai_client = AsyncOpenAI(api_key=settings.openai_api_key)
        except ImportError:
            log.warning("openai package not installed")
    return _openai_client


def _get_anthropic_client():
    global _anthropic_client
    if _anthropic_client is None and settings.anthropic_api_key:
        try:
            from anthropic import AsyncAnthropic
            _anthropic_client = AsyncAnthropic(api_key=settings.anthropic_api_key)
        except ImportError:
            log.warning("anthropic package not installed")
    return _anthropic_client


class LLMService:
    def __init__(self, provider: str | None = None, model: str | None = None):
        self.provider = provider or settings.llm_provider
        self.model = model or self._default_model()
        self._cache: dict[str, str] = {}
        self._ollama_reachable: bool | None = None
        self._ollama_checked_at: float = 0.0

    def _default_model(self) -> str:
        defaults = {
            "openai": "gpt-4o-mini",
            "anthropic": "claude-sonnet-4-20250514",
            "ollama": settings.ollama_chat_model,
        }
        return defaults.get(self.provider, "gpt-4o-mini")

    @property
    def is_available(self) -> bool:
        if self.provider == "openai":
            return bool(settings.openai_api_key)
        elif self.provider == "anthropic":
            return bool(settings.anthropic_api_key)
        elif self.provider == "ollama":
            return self._check_ollama_reachable()
        return False

    def _check_ollama_reachable(self) -> bool:
        """Ollama has no API key to gate on, so probe the socket instead. Without this,
        every citizen's decide/reflect step would attempt (and fail) a real connection
        every tick once Ollama is unreachable — the cost scales with population and
        dominates tick time at a few hundred citizens. Cached for _OLLAMA_PROBE_TTL_SECONDS
        so the cost is one bounded probe per window, not one per citizen."""
        now = time.monotonic()
        if self._ollama_reachable is not None and (now - self._ollama_checked_at) < _OLLAMA_PROBE_TTL_SECONDS:
            return self._ollama_reachable

        parsed = urlparse(settings.ollama_base_url)
        host = parsed.hostname or "localhost"
        port = parsed.port or 11434
        try:
            with socket.create_connection((host, port), timeout=0.3):
                self._ollama_reachable = True
        except OSError:
            self._ollama_reachable = False
        self._ollama_checked_at = now
        return self._ollama_reachable

    async def chat(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 500,
        system: str | None = None,
    ) -> str | None:
        if not self.is_available:
            return None

        cache_key = self._cache_key(messages, temperature, system)
        if cache_key in self._cache:
            return self._cache[cache_key]

        try:
            result = await self._call_provider(messages, temperature, max_tokens, system)
            if result:
                self._cache[cache_key] = result
                if len(self._cache) > 500:
                    keys = list(self._cache.keys())
                    for k in keys[:100]:
                        del self._cache[k]
            return result
        except Exception as e:
            log.error("llm_call_failed", provider=self.provider, error=str(e))
            return None

    async def _call_provider(
        self,
        messages: list[dict[str, str]],
        temperature: float,
        max_tokens: int,
        system: str | None,
    ) -> str | None:
        if self.provider == "openai":
            return await self._call_openai(messages, temperature, max_tokens, system)
        elif self.provider == "anthropic":
            return await self._call_anthropic(messages, temperature, max_tokens, system)
        elif self.provider == "ollama":
            return await self._call_ollama(messages, temperature, max_tokens, system)
        return None

    async def _call_openai(
        self, messages: list[dict], temperature: float, max_tokens: int, system: str | None
    ) -> str | None:
        client = _get_openai_client()
        if not client:
            return None

        all_messages = []
        if system:
            all_messages.append({"role": "system", "content": system})
        all_messages.extend(messages)

        response = await client.chat.completions.create(
            model=self.model,
            messages=all_messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return response.choices[0].message.content

    async def _call_anthropic(
        self, messages: list[dict], temperature: float, max_tokens: int, system: str | None
    ) -> str | None:
        client = _get_anthropic_client()
        if not client:
            return None

        kwargs: dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if system:
            kwargs["system"] = system

        response = await client.messages.create(**kwargs)
        return response.content[0].text

    async def _call_ollama(
        self, messages: list[dict], temperature: float, max_tokens: int, system: str | None
    ) -> str | None:
        import httpx

        all_messages = []
        if system:
            all_messages.append({"role": "system", "content": system})
        all_messages.extend(messages)

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{settings.ollama_base_url}/api/chat",
                json={
                    "model": self.model,
                    "messages": all_messages,
                    "options": {"temperature": temperature, "num_predict": max_tokens},
                    "stream": False,
                },
                timeout=60,
            )
            response.raise_for_status()
            data = response.json()
            return data.get("message", {}).get("content")

    async def generate_json(
        self,
        prompt: str,
        schema_hint: str = "",
        system: str | None = None,
        temperature: float = 0.5,
    ) -> dict | None:
        full_system = (system or "") + (
            "\n\nYou must respond with valid JSON only. No markdown, no explanation."
        )
        if schema_hint:
            full_system += f"\n\nExpected JSON shape:\n{schema_hint}"

        result = await self.chat(
            messages=[{"role": "user", "content": prompt}],
            system=full_system.strip(),
            temperature=temperature,
            max_tokens=1000,
        )
        if not result:
            return None

        result = result.strip()
        if result.startswith("```"):
            lines = result.split("\n")
            result = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])

        try:
            return json.loads(result)
        except json.JSONDecodeError:
            log.warning("llm_json_parse_failed", raw=result[:200])
            return None

    async def get_embedding(self, text: str) -> list[float] | None:
        if self.provider == "openai":
            return await self._openai_embedding(text)
        elif self.provider == "ollama":
            return await self._ollama_embedding(text)
        return None

    async def get_embeddings_batch(self, texts: list[str]) -> list[list[float]] | None:
        if self.provider == "openai":
            return await self._openai_embeddings_batch(texts)
        results = []
        for text in texts:
            emb = await self.get_embedding(text)
            if emb is None:
                return None
            results.append(emb)
        return results

    async def _openai_embedding(self, text: str) -> list[float] | None:
        client = _get_openai_client()
        if not client:
            return None
        response = await client.embeddings.create(
            model="text-embedding-3-small",
            input=text,
        )
        return response.data[0].embedding

    async def _openai_embeddings_batch(self, texts: list[str]) -> list[list[float]] | None:
        client = _get_openai_client()
        if not client:
            return None
        response = await client.embeddings.create(
            model="text-embedding-3-small",
            input=texts,
        )
        return [d.embedding for d in sorted(response.data, key=lambda d: d.index)]

    async def _ollama_embedding(self, text: str) -> list[float] | None:
        import httpx
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{settings.ollama_base_url}/api/embeddings",
                json={"model": settings.ollama_embed_model, "prompt": text},
                timeout=30,
            )
            response.raise_for_status()
            return response.json().get("embedding")

    def _cache_key(self, messages: list[dict], temperature: float, system: str | None) -> str:
        content = json.dumps({"m": messages, "t": temperature, "s": system}, sort_keys=True)
        return hashlib.md5(content.encode()).hexdigest()


_default_llm: LLMService | None = None


def get_llm_service() -> LLMService:
    global _default_llm
    if _default_llm is None:
        _default_llm = LLMService()
    return _default_llm
