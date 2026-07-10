"""POST /admin/ingest via TestClient (ingests the real vault, fake embedder)."""

from __future__ import annotations

from fastapi.testclient import TestClient
from halflight.api.deps import get_embedder
from halflight.db import get_session
from halflight.main import app
from sqlmodel import Session

from .conftest import FakeEmbedder


def test_admin_ingest_ok(session: Session, fake_embedder: FakeEmbedder) -> None:
    app.dependency_overrides[get_session] = lambda: session
    app.dependency_overrides[get_embedder] = lambda: fake_embedder
    try:
        client = TestClient(app)
        resp = client.post("/admin/ingest")
        assert resp.status_code == 200
        body = resp.json()
        assert body["ok"] is True
        assert body["errors"] == []
        assert "ingest:" in body["summary"]
    finally:
        app.dependency_overrides.clear()
