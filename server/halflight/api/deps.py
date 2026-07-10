"""FastAPI dependencies. Tests override these with fakes / a rolled-back session."""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends
from sqlmodel import Session

from halflight.config import get_settings
from halflight.db import get_session
from halflight.gm.client import LlamaClient, LLMClient
from halflight.ingest.embedder import Embedder, LlamaEmbedder


def get_chat() -> LLMClient:
    return LlamaClient(get_settings().llama_chat_url)


def get_embedder() -> Embedder:
    return LlamaEmbedder(get_settings().llama_embed_url)


SessionDep = Annotated[Session, Depends(get_session)]
ChatDep = Annotated[LLMClient, Depends(get_chat)]
EmbedderDep = Annotated[Embedder, Depends(get_embedder)]
