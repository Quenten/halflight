"""HTTP client for the llama.cpp chat server.

Two calls per turn: a grammar-constrained `complete` (intent parsing) and a
streaming `chat_stream` (narration). `LLMClient` is the interface the GM code
depends on; tests inject a fake so nothing here needs a running model.
"""

from __future__ import annotations

import json
from collections.abc import Iterator
from typing import Protocol

import httpx


class LLMClient(Protocol):
    def complete(
        self, prompt: str, *, grammar: str | None = None, temperature: float = 0.2,
        n_predict: int = 200,
    ) -> str: ...

    def chat_stream(
        self, messages: list[dict[str, str]], *, temperature: float = 0.8, max_tokens: int = 300,
    ) -> Iterator[str]: ...


class LlamaClient:
    """Talks to `llama-server` (Qwen chat). `/completion` for grammar-constrained
    parsing, OpenAI-compatible `/v1/chat/completions` (streamed) for narration."""

    def __init__(self, base_url: str, *, timeout: float = 120.0) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def complete(
        self, prompt: str, *, grammar: str | None = None, temperature: float = 0.2,
        n_predict: int = 200,
    ) -> str:
        payload: dict[str, object] = {
            "prompt": prompt,
            "temperature": temperature,
            "n_predict": n_predict,
            "cache_prompt": True,
        }
        if grammar:
            payload["grammar"] = grammar
        resp = httpx.post(f"{self.base_url}/completion", json=payload, timeout=self.timeout)
        resp.raise_for_status()
        content = resp.json()["content"]
        return str(content)

    def chat_stream(
        self, messages: list[dict[str, str]], *, temperature: float = 0.8, max_tokens: int = 300,
    ) -> Iterator[str]:
        payload = {
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": True,
            "cache_prompt": True,
        }
        with httpx.stream(
            "POST", f"{self.base_url}/v1/chat/completions", json=payload, timeout=self.timeout
        ) as resp:
            resp.raise_for_status()
            for line in resp.iter_lines():
                if not line.startswith("data:"):
                    continue
                data = line[len("data:") :].strip()
                if data == "[DONE]":
                    break
                try:
                    obj = json.loads(data)
                except json.JSONDecodeError:
                    continue
                delta = obj["choices"][0]["delta"].get("content")
                if delta:
                    yield delta
