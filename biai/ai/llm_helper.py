"""Unified LLM helper with disk cache for Ollama calls."""

import hashlib
import json
import time
from pathlib import Path
from typing import AsyncIterator

import httpx

from biai.config.constants import DEFAULT_MODEL, DEFAULT_OLLAMA_HOST
from biai.utils.logger import get_logger

logger = get_logger(__name__)

_CACHE_DIR = Path.home() / ".biai" / "llm_cache"
_DEFAULT_TTL = 3600  # 1 hour


class LLMHelper:
    """Unified LLM caller with disk cache and streaming support."""

    def __init__(
        self,
        ollama_host: str = DEFAULT_OLLAMA_HOST,
        ollama_model: str = DEFAULT_MODEL,
        cache_dir: Path | None = None,
    ):
        self._host = ollama_host
        self._model = ollama_model
        self._cache_dir = cache_dir or _CACHE_DIR
        self._cache_dir.mkdir(parents=True, exist_ok=True)

    async def generate_json(
        self,
        prompt: str,
        cache_key: str = "",
        timeout: float = 30.0,
        ttl: int = _DEFAULT_TTL,
    ) -> dict:
        """Generate JSON response from LLM with optional disk cache.

        Args:
            prompt: The prompt to send.
            cache_key: Cache key for deduplication. Empty = no caching.
            timeout: HTTP timeout in seconds.
            ttl: Cache time-to-live in seconds.

        Returns:
            Parsed JSON dict, or empty dict on failure.
        """
        if cache_key:
            cached = self._read_cache(cache_key, ttl)
            if cached is not None:
                logger.debug("llm_cache_hit", key=cache_key[:40])
                return cached

        text = await self.generate_text(prompt, timeout=timeout)
        if not text:
            return {}

        parsed = _parse_json(text)
        if parsed and cache_key:
            self._write_cache(cache_key, parsed)

        return parsed

    async def generate_text(
        self,
        prompt: str,
        timeout: float = 30.0,
        system: str = "",
    ) -> str:
        """Generate text response from Ollama (non-streaming)."""
        payload: dict = {
            "model": self._model,
            "prompt": prompt,
            "stream": False,
        }
        if system:
            payload["system"] = system

        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    f"{self._host}/api/generate",
                    json=payload,
                    timeout=timeout,
                )
                resp.raise_for_status()
                data = resp.json()
                return data.get("response", "")
        except Exception as e:
            logger.warning("llm_generate_failed", error=str(e))
            return ""

    async def generate_stream(
        self,
        prompt: str,
        timeout: float = 60.0,
        system: str = "",
    ) -> AsyncIterator[str]:
        """Stream text response from Ollama token by token."""
        payload: dict = {
            "model": self._model,
            "prompt": prompt,
            "stream": True,
        }
        if system:
            payload["system"] = system

        try:
            async with httpx.AsyncClient() as client:
                async with client.stream(
                    "POST",
                    f"{self._host}/api/generate",
                    json=payload,
                    timeout=timeout,
                ) as resp:
                    resp.raise_for_status()
                    async for line in resp.aiter_lines():
                        if not line.strip():
                            continue
                        try:
                            data = json.loads(line)
                            if token := data.get("response", ""):
                                yield token
                            if data.get("done", False):
                                break
                        except json.JSONDecodeError:
                            continue
        except Exception as e:
            logger.error("llm_stream_failed", error=str(e))
            yield f"Error: {e}"

    # ------------------------------------------------------------------
    # Cache helpers
    # ------------------------------------------------------------------

    def _cache_path(self, key: str) -> Path:
        h = hashlib.sha256(key.encode()).hexdigest()[:16]
        return self._cache_dir / f"{h}.json"

    def _read_cache(self, key: str, ttl: int) -> dict | None:
        path = self._cache_path(key)
        if not path.exists():
            return None
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            ts = data.get("_ts", 0)
            if time.time() - ts > ttl:
                path.unlink(missing_ok=True)
                return None
            return data.get("value", {})
        except (json.JSONDecodeError, OSError):
            path.unlink(missing_ok=True)
            return None

    def _write_cache(self, key: str, value: dict) -> None:
        path = self._cache_path(key)
        try:
            path.write_text(
                json.dumps({"_ts": time.time(), "value": value}),
                encoding="utf-8",
            )
        except OSError as e:
            logger.debug("llm_cache_write_failed", error=str(e))

    def clear_cache(self) -> int:
        """Remove all cached responses. Returns count of removed files."""
        count = 0
        for f in self._cache_dir.glob("*.json"):
            f.unlink(missing_ok=True)
            count += 1
        return count


def _parse_json(text: str) -> dict:
    """Extract JSON from LLM response (handles markdown fences)."""
    text = text.strip()

    # Try direct parse
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Try extracting from markdown code fence
    import re
    match = re.search(r"```(?:json)?\s*\n?(.*?)\n?```", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1).strip())
        except json.JSONDecodeError:
            pass

    # Try finding first { ... } block
    start = text.find("{")
    end = text.rfind("}")
    if start >= 0 and end > start:
        try:
            return json.loads(text[start:end + 1])
        except json.JSONDecodeError:
            pass

    return {}
