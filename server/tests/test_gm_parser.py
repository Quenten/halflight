"""Intent parser: mocked LLM client, no server needed."""

from __future__ import annotations

from collections.abc import Iterator

from halflight.engine.actions import Attack, Custom, Move
from halflight.engine.gamestate import GameState, LocationView, NpcView, PlayerView
from halflight.gm.parser import parse_intent, render_scene


class FakeClient:
    def __init__(self, responses: list[str]) -> None:
        self._responses = list(responses)

    def complete(
        self, prompt: str, *, grammar: str | None = None, temperature: float = 0.2,
        n_predict: int = 200,
    ) -> str:
        return self._responses.pop(0)

    def chat_stream(
        self, messages: list[dict[str, str]], *, temperature: float = 0.8, max_tokens: int = 300,
    ) -> Iterator[str]:
        yield from ()


def make_state() -> GameState:
    return GameState(
        player=PlayerView(hp=15, location_id="loc_a", stats={}, inventory={"itm_shiv": 1}),
        location=LocationView(id="loc_a", connections=["loc_b"]),
        npcs={"npc_dax": NpcView(id="npc_dax", hp=15, stats={}, location_id="loc_a")},
    )


def test_parses_valid_action() -> None:
    client = FakeClient(['{"kind": "move", "target": "loc_b"}'])
    action = parse_intent("go north", make_state(), client, system="SYS")
    assert isinstance(action, Move) and action.target == "loc_b"


def test_retries_then_succeeds() -> None:
    client = FakeClient(["not json", '{"kind": "attack", "target": "npc_dax"}'])
    action = parse_intent("hit dax", make_state(), client, system="SYS")
    assert isinstance(action, Attack) and action.target == "npc_dax"


def test_falls_back_to_custom() -> None:
    client = FakeClient(["garbage", "still garbage"])
    action = parse_intent("do a barrel roll", make_state(), client, system="SYS")
    assert isinstance(action, Custom) and action.description == "do a barrel roll"


def test_render_scene_lists_ids() -> None:
    scene = render_scene(make_state())
    assert "loc_b" in scene and "npc_dax" in scene and "itm_shiv" in scene
