"""Narrator, fact-check, context assembly, and turn logging — no server."""

from __future__ import annotations

import json
from collections.abc import Iterator
from pathlib import Path

from halflight.engine.actions import Attack, Move
from halflight.engine.gamestate import GameState, LocationView, NpcView, PlayerView
from halflight.engine.results import SceneEvent, StateChange, TurnResult
from halflight.gm.context import build_context
from halflight.gm.narrator import check_consistency, factual_fallback, narrate
from halflight.gm.retrieval import RetrievedChunk
from halflight.gm.turnlog import log_turn


class FakeChatClient:
    def __init__(self, chat_responses: list[str]) -> None:
        self._chat = list(chat_responses)

    def complete(
        self, prompt: str, *, grammar: str | None = None, temperature: float = 0.2,
        n_predict: int = 200,
    ) -> str:
        return ""

    def chat_stream(
        self, messages: list[dict[str, str]], *, temperature: float = 0.8, max_tokens: int = 300,
    ) -> Iterator[str]:
        yield from self._chat.pop(0)


def _attack_miss() -> TurnResult:
    return TurnResult(
        action=Attack(target="npc_dax"),
        valid=True,
        roll=4,
        difficulty=12,
        outcome="failure",
        scene_events=[SceneEvent(kind="attack_miss", detail={"npc": "npc_dax"})],
        significance=1,
    )


def _move_ok() -> TurnResult:
    return TurnResult(
        action=Move(target="loc_b"),
        valid=True,
        outcome="success",
        state_changes=[StateChange(entity="player", field="location_id", delta="loc_b")],
        scene_events=[SceneEvent(kind="moved", detail={"from": "loc_a", "to": "loc_b"})],
    )


def test_clean_narration_returned() -> None:
    client = FakeChatClient(["You stepped onto the platform. Coolant hissed somewhere below."])
    out = narrate(client, system="SYS", context="CTX", result=_move_ok())
    assert "platform" in out


def test_regenerates_on_contradiction() -> None:
    # First narration claims a hit on a failed attack; second is clean.
    client = FakeChatClient(
        ["Your knife sank in deep.", "You lunged, but the blade found only air."]
    )
    out = narrate(client, system="SYS", context="CTX", result=_attack_miss())
    assert "air" in out


def test_falls_back_to_factual_when_both_bad() -> None:
    client = FakeChatClient(["Your knife sank in.", "You killed him where he stood."])
    out = narrate(client, system="SYS", context="CTX", result=_attack_miss())
    assert out == factual_fallback(_attack_miss())
    assert "missed" in out.lower()


def test_check_consistency_flags_and_passes() -> None:
    assert check_consistency("your knife sinks in", _attack_miss())
    assert not check_consistency("you swung wide and hit nothing", _attack_miss())


def test_build_context_includes_lore_and_result() -> None:
    state = GameState(
        player=PlayerView(hp=15, location_id="loc_a", stats={}),
        location=LocationView(id="loc_a"),
        npcs={"npc_dax": NpcView(id="npc_dax", hp=15, stats={}, location_id="loc_a")},
    )
    chunks = [RetrievedChunk("lore_x", "lore", "The Saltline runs the under-levels.", 0.1)]
    ctx = build_context(state, _move_ok(), chunks)
    assert "Saltline" in ctx
    assert "outcome: success" in ctx
    assert "npc_dax" in ctx


def test_empty_retrieval_states_ignorance() -> None:
    state = GameState(player=PlayerView(hp=15, location_id="loc_a", stats={}),
                      location=LocationView(id="loc_a"))
    ctx = build_context(state, _move_ok(), [])
    assert "does not know" in ctx


def test_log_turn_writes_file(tmp_path: Path) -> None:
    path = log_turn(
        tmp_path, run_id=7, turn_no=3,
        player_text="hit dax", parse_prompt="P", parse_output='{"kind":"attack"}',
        narration_context="CTX", narration="You missed.",
        action={"kind": "attack"}, result={"outcome": "failure"},
    )
    assert path == tmp_path / "turns" / "7" / "3.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["player_text"] == "hit dax"
    assert data["narration"]["text"] == "You missed."
