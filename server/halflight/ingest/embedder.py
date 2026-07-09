"""Embedding client for the bge-m3 llama.cpp server.

`Embedder` is the interface ingestion depends on; tests inject a fake. The real
implementation calls the OpenAI-compatible `/v1/embeddings` endpoint exposed by
`llama-server --embedding`.
"""

from __future__ import annotations

from typing import Protocol

import httpx

from halflight.models.authored import EMBED_DIM


class Embedder(Protocol):
    def embed(self, texts: list[str]) -> list[list[float]]:
        """Return one EMBED_DIM vector per input text, in the same order."""
        ...


class LlamaEmbedder:
    def __init__(self, base_url: str, *, dim: int = EMBED_DIM, timeout: float = 60.0) -> None:
        self.base_url = base_url.rstrip("/")
        self.dim = dim
        self.timeout = timeout

    def embed(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        resp = httpx.post(
            f"{self.base_url}/v1/embeddings",
            json={"input": texts},
            timeout=self.timeout,
        )
        resp.raise_for_status()
        data = resp.json()["data"]
        # Preserve request order (endpoint returns an "index" per item).
        ordered = sorted(data, key=lambda d: d["index"])
        vectors = [d["embedding"] for d in ordered]
        if len(vectors) != len(texts):
            raise ValueError(f"embedder returned {len(vectors)} vectors for {len(texts)} texts")
        for v in vectors:
            if len(v) != self.dim:
                raise ValueError(f"embedder returned dim {len(v)}, expected {self.dim}")
        return vectors
