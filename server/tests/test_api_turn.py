"""POST /turn SSE via TestClient with a fake LLM and rolled-back session."""

from __future__ import annotations

import json
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient
from halflight.api.deps import get_chat, get_embedder
from halflight.db import get_session
from halflight.engine.turn import start_run
from halflight.ingest.runner import run_ingest
from halflight.main import app
from sqlmodel import Session

from .conftest import FakeEmbedder

FIXTURE = Path(__file__).parent / "fixtures" / "vault_mini"
STATS = {"muscle": 10, "nerve": 10, "wits": 10, "tech": 10, "streetwise": 10, "presence": 10}


class FakeGM:
    def __init__(self, complete_responses: list[str], narration: str) -> None:
        self._complete = list(complete_responses)
        self._narration = narration

    def complete(
        self, prompt: str, *, grammar: str | None = None, temperature: float = 0.2,
        n_predict: int = 200,
    ) -> str:
        return self._complete.pop(0)

    def chat_stream(
        self, messages: list[dict[str, str]], *, temperature: float = 0.8, max_tokens: int = 300,
    ) -> Iterator[str]:
        # stream token by token
        for word in self._narration.split(" "):
            yield word + " "


def parse_sse(text: str) -> list[dict[str, Any]]:
    events = []
    for block in text.strip().split("\n\n"):
        ev: dict[str, Any] = {}
        for line in block.splitlines():
            if line.startswith("event:"):
                ev["event"] = line[6:].strip()
            elif line.startswith("data:"):
                ev["data"] = json.loads(line[5:].strip())
        if ev:
            events.append(ev)
    return events


@pytest.fixture
def wired(session: Session, fake_embedder: FakeEmbedder) -> Iterator[tuple[int, Any]]:
    run_ingest(FIXTURE, session, fake_embedder)
    run_id = start_run(
        session, character_name="Vex", start_location="loc_tram_hub", stats=STATS, hp=15
    )
    app.dependency_overrides[get_session] = lambda: session
    app.dependency_overrides[get_embedder] = lambda: fake_embedder

    def _use(chat: FakeGM) -> TestClient:
        app.dependency_overrides[get_chat] = lambda: chat
        return TestClient(app)

    try:
        yield run_id, _use
    finally:
        app.dependency_overrides.clear()


def test_turn_streams_narration_and_state(wired: Any) -> None:
    run_id, use = wired
    chat = FakeGM(['{"kind": "talk", "target": "npc_dax"}'], "Dax grunted, eyes on the gate.")
    client = use(chat)
    resp = client.post("/turn", json={"run_id": run_id, "text": "ask dax about the tram"})
    assert resp.status_code == 200
    events = parse_sse(resp.text)

    kinds = [e["event"] for e in events]
    assert "token" in kinds and "state" in kinds and kinds[-1] == "done"
    assert "correction" not in kinds

    narration = "".join(e["data"]["text"] for e in events if e["event"] == "token")
    assert "Dax grunted" in narration
    state = next(e["data"] for e in events if e["event"] == "state")
    assert state["run_id"] == run_id


def test_turn_appends_correction_on_contradiction(wired: Any) -> None:
    run_id, use = wired
    # Talk is narrative_only; a narration claiming a kill contradicts it.
    chat = FakeGM(['{"kind": "talk", "target": "npc_dax"}'], "You killed him on the spot.")
    client = use(chat)
    resp = client.post("/turn", json={"run_id": run_id, "text": "talk to dax"})
    events = parse_sse(resp.text)
    correction = next((e for e in events if e["event"] == "correction"), None)
    assert correction is not None
    assert "traded words" in correction["data"]["text"]


def test_turn_unknown_run_404(wired: Any) -> None:
    _, use = wired
    client = use(FakeGM(["{}"], "x"))
    assert client.post("/turn", json={"run_id": 999999, "text": "hi"}).status_code == 404
