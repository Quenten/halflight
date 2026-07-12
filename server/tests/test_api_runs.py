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


def test_history_replays_turns_oldest_first(
    client: TestClient, session: Session, fake_embedder: FakeEmbedder
) -> None:
    from halflight.engine.turn import start_run
    from halflight.models import Narration
    from halflight.models.runtime import utcnow

    run_ingest(FIXTURE, session, fake_embedder)
    run_id = start_run(
        session, character_name="Vex", start_location="loc_tram_hub",
        stats={"muscle": 10}, hp=15,
    )
    for turn_no, (pt, body) in enumerate(
        [("look around", "The deck hums."), ("ask dax", "Dax grunts.")], start=1
    ):
        session.add(
            Narration(run_id=run_id, turn_no=turn_no, player_text=pt, body=body, ts=utcnow())
        )
    session.flush()

    turns = client.get("/history", params={"run_id": run_id}).json()["turns"]
    assert [t["turn_no"] for t in turns] == [1, 2]  # oldest first
    assert turns[0]["player_text"] == "look around"
    assert turns[1]["narration"] == "Dax grunts."


def test_history_empty_for_new_run(client: TestClient) -> None:
    assert client.get("/history", params={"run_id": 424242}).json()["turns"] == []


def test_chargen_data(client: TestClient) -> None:
    data = client.get("/chargen").json()
    assert len(data["classes"]) == 4
    assert [s["id"] for s in data["steps"]] == ["upbringing", "marked", "ran_with", "last_job"]


def test_create_run_via_chargen(
    client: TestClient, session: Session, fake_embedder: FakeEmbedder
) -> None:
    run_ingest(FIXTURE, session, fake_embedder)
    body = {
        "character_name": "Vex",
        "class_id": "fixer",
        "choices": {
            "upbringing": "sump", "marked": "ambition",
            "ran_with": "fixer", "last_job": "runner",
        },
    }
    resp = client.post("/runs/chargen", json=body)
    assert resp.status_code == 200
    out = resp.json()
    assert out["state"]["character_name"] == "Vex"
    assert out["state"]["stats"]["streetwise"] >= 15  # fixer 15 + sump upbringing +1
    assert len(out["backstory"]) == 4
    # The backstory is distilled into a persisted origin blurb, shown on the sheet.
    assert out["state"]["origin"]
    assert len(out["state"]["origin"]) > 20


def test_chargen_unknown_class_400(client: TestClient) -> None:
    resp = client.post("/runs/chargen", json={"character_name": "X", "class_id": "nope"})
    assert resp.status_code == 400
