"""/runs + /state via TestClient, backed by the rolled-back session."""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from halflight.db import get_session
from halflight.ingest.runner import run_ingest
from halflight.main import app
from sqlmodel import Session

from .conftest import FakeEmbedder

FIXTURE = Path(__file__).parent / "fixtures" / "vault_mini"


@pytest.fixture
def client(session: Session) -> Iterator[TestClient]:
    app.dependency_overrides[get_session] = lambda: session
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()


def test_create_run_and_get_state(
    client: TestClient, session: Session, fake_embedder: FakeEmbedder
) -> None:
    run_ingest(FIXTURE, session, fake_embedder)

    resp = client.post("/runs", json={"start_location": "loc_tram_hub", "character_name": "Vex"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["location_id"] == "loc_tram_hub"
    assert data["hp"] == 15
    assert data["ended"] is False
    assert data["location_name"] == "Tram Hub"
    assert any(e["id"] == "loc_underlevel" for e in data["exits"])
    assert any(n["id"] == "npc_dax" and n["name"] == "Dax" for n in data["npcs"])

    run_id = data["run_id"]
    state = client.get("/state", params={"run_id": run_id})
    assert state.status_code == 200
    assert state.json()["run_id"] == run_id


def test_state_unknown_run_404(client: TestClient) -> None:
    assert client.get("/state", params={"run_id": 999999}).status_code == 404
