"""Full GM turn end-to-end with mocked LLM: parse -> engine -> narrate -> log.

Game data comes from ingested vault_mini; prompt assets come from the real
vault/rules (which vault_mini doesn't carry). No model server needed.
"""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

from halflight.engine.dice import Dice
from halflight.engine.turn import start_run
from halflight.gm.loop import play_turn
from halflight.ingest.runner import run_ingest
from sqlmodel import Session

from .conftest import FakeEmbedder

FIXTURE = Path(__file__).parent / "fixtures" / "vault_mini"
REPO_VAULT = str(Path(__file__).parents[2] / "vault")
STATS = {"muscle": 10, "nerve": 10, "wits": 10, "tech": 10, "streetwise": 10, "presence": 10}


class FakeGM:
    def __init__(self, complete_responses: list[str], chat_responses: list[str]) -> None:
        self._complete = list(complete_responses)
        self._chat = list(chat_responses)

    def complete(
        self, prompt: str, *, grammar: str | None = None, temperature: float = 0.2,
        n_predict: int = 200,
    ) -> str:
        return self._complete.pop(0)

    def chat_stream(
        self, messages: list[dict[str, str]], *, temperature: float = 0.8, max_tokens: int = 300,
    ) -> Iterator[str]:
        yield from self._chat.pop(0)


def test_play_turn_parses_resolves_narrates_logs(
    session: Session, fake_embedder: FakeEmbedder, tmp_path: Path
) -> None:
    run_ingest(FIXTURE, session, fake_embedder)
    run_id = start_run(
        session, character_name="Vex", start_location="loc_tram_hub", stats=STATS, hp=15
    )

    chat = FakeGM(
        ['{"kind": "talk", "target": "npc_dax"}'],
        ["Dax barely looked up from the fare booth, thumbs working the ledger."],
    )
    played = play_turn(
        session, run_id, "ask dax about the docks",
        chat=chat, embedder=fake_embedder, vault_path=REPO_VAULT, logs_dir=tmp_path,
    )

    assert played.action.kind == "talk"
    assert played.result.outcome == "narrative_only"
    assert "Dax" in played.narration
    assert played.turn_no == 1
    assert (tmp_path / "turns" / str(run_id) / "1.json").exists()


def test_play_turn_unparseable_falls_back_to_custom(
    session: Session, fake_embedder: FakeEmbedder, tmp_path: Path
) -> None:
    run_ingest(FIXTURE, session, fake_embedder)
    run_id = start_run(
        session, character_name="Vex", start_location="loc_tram_hub", stats=STATS, hp=15
    )
    # Parser returns junk twice -> Custom fallback; engine still produces a result.
    chat = FakeGM(["junk", "junk"], ["You tried something odd. Nothing came of it."])
    played = play_turn(
        session, run_id, "recite a poem to the ceiling",
        chat=chat, embedder=fake_embedder, vault_path=REPO_VAULT, logs_dir=tmp_path,
        dice=Dice(0),
    )
    assert played.action.kind == "custom"
    assert played.result.valid
