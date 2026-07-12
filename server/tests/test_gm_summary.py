"""Episodic summary: older turns compress into facts/promises/threads."""

from __future__ import annotations

import json
from collections.abc import Iterator
from pathlib import Path

from halflight.engine.turn import start_run
from halflight.gm.summary import (
    KEEP_VERBATIM,
    SUMMARY_INTERVAL,
    format_summary,
    latest_summary,
    maybe_summarize,
)
from halflight.ingest.runner import run_ingest
from halflight.models import Event
from halflight.models.runtime import utcnow
from sqlmodel import Session

from .conftest import FakeEmbedder

FIXTURE = Path(__file__).parent / "fixtures" / "vault_mini"
STATS = {"muscle": 10, "nerve": 10, "wits": 10, "tech": 10, "streetwise": 10, "presence": 10}


class FakeSummaryChat:
    def __init__(self, payload: dict[str, list[str]]) -> None:
        self._payload = json.dumps(payload)

    def complete(self, prompt: str, **kw: object) -> str:
        return ""

    def chat_stream(self, messages: list[dict[str, str]], **kw: object) -> Iterator[str]:
        yield self._payload


def _seed_turns(session: Session, run_id: int, n: int) -> None:
    for t in range(1, n + 1):
        session.add(
            Event(run_id=run_id, turn_no=t, action={"kind": "move"},
                  result={"outcome": "success", "scene_events": []},
                  significance=0, location_id="loc_tram_hub", ts=utcnow())
        )
    session.commit()


def test_summarizes_after_interval(session: Session, fake_embedder: FakeEmbedder) -> None:
    run_ingest(FIXTURE, session, fake_embedder)
    run_id = start_run(
        session, character_name="Vex", start_location="loc_tram_hub", stats=STATS, hp=15
    )
    _seed_turns(session, run_id, SUMMARY_INTERVAL + KEEP_VERBATIM)
    chat = FakeSummaryChat({"facts_established": ["Dax skims fares"], "promises_made": [],
                            "open_threads": ["the shaft is unguarded"]})

    wrote = maybe_summarize(session, chat, run_id, SUMMARY_INTERVAL + KEEP_VERBATIM)
    assert wrote is True

    body = latest_summary(session, run_id)
    assert body is not None and "Dax skims fares" in body["facts_established"]
    story = format_summary(body)
    assert story is not None and "Dax skims fares" in story


def test_no_summary_before_interval(session: Session, fake_embedder: FakeEmbedder) -> None:
    run_id = start_run(
        session, character_name="Vex", start_location="loc_tram_hub", stats=STATS, hp=15
    )
    _seed_turns(session, run_id, 3)
    chat = FakeSummaryChat({"facts_established": [], "promises_made": [], "open_threads": []})
    assert maybe_summarize(session, chat, run_id, 3) is False
    assert latest_summary(session, run_id) is None
