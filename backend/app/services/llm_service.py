"""
Ollama LLM service — fast async client with two speed tiers.

- FAST (analysis) tier: 30s timeout, 400 tokens, used during agent runs
- FULL (chat/docs) tier: 120s timeout, 2048 tokens, used for chat/reports
"""
from __future__ import annotations

import asyncio
import json
from typing import AsyncIterator, Dict, List, Optional

import httpx

from app.core.config import settings
from app.core.logging import get_logger, log_event
from app.utils.filesystem import truncate


logger = get_logger("codeguardian.llm")


class LLMError(RuntimeError):
    pass


class OllamaClient:
    def __init__(
        self,
        base_url: Optional[str] = None,
        default_model: Optional[str] = None,
        fallback_model: Optional[str] = None,
        timeout: Optional[int] = None,
        max_tokens: Optional[int] = None,
    ) -> None:
        self.base_url = (base_url or settings.ollama_base_url).rstrip("/")
        self.default_model = default_model or settings.ollama_default_model
        self.fallback_model = fallback_model or settings.ollama_fallback_model
        self.timeout = timeout or settings.llm_timeout_sec
        self.max_tokens = max_tokens or settings.llm_max_tokens

    async def list_models(self) -> List[str]:
        async with httpx.AsyncClient(timeout=5.0) as client:
            r = await client.get(f"{self.base_url}/api/tags")
            r.raise_for_status()
            return [m["name"] for m in r.json().get("models", [])]

    async def is_available(self) -> bool:
        try:
            await self.list_models()
            return True
        except Exception as e:
            log_event(logger, 30, "ollama_unavailable", error=str(e))
            return False

    async def generate(
        self,
        prompt: str,
        *,
        model: Optional[str] = None,
        system: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        json_mode: bool = False,
    ) -> str:
        body: Dict = {
            "model": model or self.default_model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature if temperature is not None else settings.llm_temperature,
                "num_predict": max_tokens or self.max_tokens,
                # Disable mirostat to reduce latency
                "mirostat": 0,
            },
        }
        if system:
            body["system"] = system
        if json_mode:
            body["format"] = "json"

        for attempt, m in enumerate([body["model"], self.fallback_model], start=1):
            body["model"] = m
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    r = await client.post(f"{self.base_url}/api/generate", json=body)
                    r.raise_for_status()
                    return (r.json().get("response") or "").strip()
            except (httpx.HTTPError, json.JSONDecodeError) as e:
                log_event(logger, 30, "ollama_failed", attempt=attempt, model=m, error=str(e))
                if attempt == 1:
                    continue
                raise LLMError(f"LLM failed: {e}") from e
        raise LLMError("LLM failed after retries")

    async def chat(
        self,
        messages: List[Dict[str, str]],
        *,
        model: Optional[str] = None,
        system: Optional[str] = None,
    ) -> str:
        msgs = list(messages)
        if system:
            msgs = [{"role": "system", "content": system}] + msgs
        body = {
            "model": model or self.default_model,
            "messages": msgs,
            "stream": False,
            "options": {"temperature": settings.llm_temperature, "num_predict": self.max_tokens},
        }
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            r = await client.post(f"{self.base_url}/api/chat", json=body)
            r.raise_for_status()
            return (r.json().get("message", {}).get("content") or "").strip()

    async def stream(self, prompt: str, *, model: Optional[str] = None,
                     system: Optional[str] = None) -> AsyncIterator[str]:
        body = {
            "model": model or self.default_model,
            "prompt": prompt,
            "stream": True,
            "options": {"temperature": settings.llm_temperature},
        }
        if system:
            body["system"] = system
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            async with client.stream("POST", f"{self.base_url}/api/generate", json=body) as r:
                r.raise_for_status()
                async for line in r.aiter_lines():
                    if not line:
                        continue
                    try:
                        data = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    if data.get("response"):
                        yield data["response"]
                    if data.get("done"):
                        return


# Two singleton clients: fast for agent analysis, full for chat/docs
_fast_client: Optional[OllamaClient] = None
_full_client: Optional[OllamaClient] = None

# Cache the availability check briefly so a down Ollama fails fast (~2s)
# instead of every agent/file re-discovering the same timeout independently
# and compounding into a multi-hour run.
_availability_cache: Dict[str, "tuple[bool, float]"] = {}
_AVAILABILITY_TTL_SEC = 15.0
_AVAILABILITY_CHECK_TIMEOUT_SEC = 2.0


async def check_ollama_available(force: bool = False) -> bool:
    """Cheap, cached reachability check (~2s worst case, not the full 30-120s tier timeout).

    Call this once before starting a batch of LLM-dependent work (e.g. an
    analysis run, or a chat request) so an unreachable Ollama fails
    immediately with a clear error instead of letting every downstream call
    retry against its full per-request timeout.
    """
    import time as _time

    key = "ollama"
    now = _time.monotonic()
    if not force and key in _availability_cache:
        ok, checked_at = _availability_cache[key]
        if now - checked_at < _AVAILABILITY_TTL_SEC:
            return ok

    client = OllamaClient(timeout=_AVAILABILITY_CHECK_TIMEOUT_SEC)
    ok = await client.is_available()
    _availability_cache[key] = (ok, now)
    return ok


def get_llm(fast: bool = False) -> OllamaClient:
    """Return the appropriate LLM client tier."""
    global _fast_client, _full_client
    if fast:
        if _fast_client is None:
            _fast_client = OllamaClient(timeout=30, max_tokens=400)
        return _fast_client
    if _full_client is None:
        _full_client = OllamaClient(timeout=120, max_tokens=2048)
    return _full_client


async def llm_complete(prompt: str, *, fast: bool = False, **kwargs) -> str:
    return await get_llm(fast=fast).generate(prompt, **kwargs)


async def llm_json(prompt: str, *, system: Optional[str] = None,
                   fast: bool = False, **kwargs) -> Dict:
    raw = await llm_complete(prompt, system=system, json_mode=True, fast=fast, **kwargs)
    raw = raw.strip().strip("`")
    if raw.startswith("json"):
        raw = raw[4:]
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        start, end = raw.find("{"), raw.rfind("}")
        if start != -1 and end > start:
            try:
                return json.loads(raw[start: end + 1])
            except json.JSONDecodeError:
                pass
        log_event(logger, 30, "llm_json_parse_failed", raw=truncate(raw, 200))
        return {}
