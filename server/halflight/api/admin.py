"""Admin endpoints: trigger vault re-ingestion."""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from halflight.api.deps import EmbedderDep, SessionDep
from halflight.config import get_settings
from halflight.ingest.runner import run_ingest

router = APIRouter(prefix="/admin")


class IngestResponse(BaseModel):
    ok: bool
    summary: str
    errors: list[str]


@router.post("/ingest", response_model=IngestResponse)
def ingest(session: SessionDep, embedder: EmbedderDep) -> IngestResponse:
    report = run_ingest(get_settings().vault_path, session, embedder)
    return IngestResponse(
        ok=not report.aborted and report.lint.ok,
        summary=report.summary(),
        errors=[str(i) for i in report.lint.errors],
    )
