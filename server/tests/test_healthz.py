"""M0 smoke test: the app boots and /healthz answers. No DB or LLM required."""

from __future__ import annotations

from fastapi.testclient import TestClient
from halflight.main import app

client = TestClient(app)


def test_healthz() -> None:
    resp = client.get("/healthz")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}
