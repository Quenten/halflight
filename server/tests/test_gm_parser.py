"""Intent parser: mocked LLM client, no server needed."""

from __future__ import annotations

from collections.abc import Iterator

from halflight.engine.actions import Attack, Custom, Investigate, Move, Talk, UseItem
from halflight.engine.gamestate import GameState, ItemView, LocationView, NpcView, PlayerView
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


def test_spurious_move_to_talk_is_guarded() -> None:
    # Model over-picks move; "ask dax" has no travel cue -> talk to the present NPC.
    client = FakeClient(['{"kind": "move", "target": "loc_b"}'])
    action = parse_intent("ask dax about the docks", make_state(), client, system="SYS")
    assert isinstance(action, Talk) and action.target == "npc_dax"


def test_spurious_move_without_npc_becomes_investigate() -> None:
    client = FakeClient(['{"kind": "move", "target": "loc_b"}'])
    action = parse_intent("what is this place", make_state(), client, system="SYS")
    assert isinstance(action, Investigate)


def test_real_move_is_kept() -> None:
    client = FakeClient(['{"kind": "move", "target": "loc_b"}'])
    action = parse_intent("head over to loc_b", make_state(), client, system="SYS")
    assert isinstance(action, Move) and action.target == "loc_b"


def test_violence_at_present_npc_forced_to_attack() -> None:
    # Model mis-reads "gun Dax down" as investigate; guard forces an attack.
    client = FakeClient(['{"kind": "investigate", "target": null}'])
    action = parse_intent("draw the pistol and gun Dax down", make_state(), client, system="SYS")
    assert isinstance(action, Attack) and action.target == "npc_dax"


def test_talk_wins_over_stray_travel_word() -> None:
    # "work going" tripped the travel guard; talking to a present NPC must still win.
    client = FakeClient(['{"kind": "move", "target": "loc_b"}'])
    action = parse_intent(
        "greet Dax and ask what work is going", make_state(), client, system="SYS"
    )
    assert isinstance(action, Talk) and action.target == "npc_dax"


def test_attacking_inflection_hits_sole_npc() -> None:
    # "keep attacking" — no name, "attack" inflected; the one person here takes it.
    client = FakeClient(['{"kind": "investigate", "target": null}'])
    action = parse_intent("I keep attacking", make_state(), client, system="SYS")
    assert isinstance(action, Attack) and action.target == "npc_dax"


def test_firing_inflection_is_attack() -> None:
    client = FakeClient(['{"kind": "investigate", "target": null}'])
    action = parse_intent("keep firing on him", make_state(), client, system="SYS")
    assert isinstance(action, Attack) and action.target == "npc_dax"


def _two_npc_state() -> GameState:
    # Two people present; you've angered the syndicate, so Dax is the hostile one.
    return GameState(
        player=PlayerView(hp=15, location_id="loc_a", stats={}),
        location=LocationView(id="loc_a", connections=["loc_b"]),
        npcs={
            "npc_dax": NpcView(
                id="npc_dax", hp=15, stats={}, location_id="loc_a", faction_id="fac_syndicate"
            ),
            "npc_thane": NpcView(
                id="npc_thane", hp=15, stats={}, location_id="loc_a", disposition=5
            ),
        },
        faction_rep={"fac_syndicate": -3},
    )


def test_followup_attack_with_crowd_hits_most_hostile() -> None:
    # The exact bug: "keep attacking" with two people present and no name used to
    # fizzle (no target resolved). It must continue the fight with whoever you angered.
    client = FakeClient(['{"kind": "investigate", "target": null}'])
    action = parse_intent("I keep attacking, no mercy", _two_npc_state(), client, system="SYS")
    assert isinstance(action, Attack) and action.target == "npc_dax"


def test_named_attack_in_crowd_hits_the_named() -> None:
    client = FakeClient(['{"kind": "investigate", "target": null}'])
    action = parse_intent("I hit Thane again", _two_npc_state(), client, system="SYS")
    assert isinstance(action, Attack) and action.target == "npc_thane"


def test_violence_about_someone_is_not_forced() -> None:
    # A question mentioning violence shouldn't become an attack.
    client = FakeClient(['{"kind": "talk", "target": "npc_dax"}'])
    action = parse_intent("ask Dax who I should kill next", make_state(), client, system="SYS")
    assert isinstance(action, Talk)


def _item_state() -> GameState:
    return GameState(
        player=PlayerView(hp=10, location_id="loc_a", stats={}, inventory={"itm_stimshot": 1}),
        location=LocationView(id="loc_a", connections=["loc_b"]),
        items={"itm_stimshot": ItemView(id="itm_stimshot", kind="consumable", name="Stimshot")},
    )


def test_use_item_guarded_from_investigate() -> None:
    # The exact bug: "use my stimshot" came back as investigate and never healed.
    client = FakeClient(['{"kind": "investigate", "target": null}'])
    action = parse_intent("I use my stimshot", _item_state(), client, system="SYS")
    assert isinstance(action, UseItem) and action.item == "itm_stimshot"


def test_use_item_id_normalized_to_inventory() -> None:
    # Model picks the item but with a bare id; repair it to the carried id.
    client = FakeClient(['{"kind": "use_item", "item": "stimshot"}'])
    action = parse_intent("jab the stim", _item_state(), client, system="SYS")
    assert isinstance(action, UseItem) and action.item == "itm_stimshot"


def test_use_verb_without_carried_item_is_not_use() -> None:
    # "drink at the bar" names no carried item — must not become a use_item.
    client = FakeClient(['{"kind": "investigate", "target": null}'])
    action = parse_intent("drink at the bar", _item_state(), client, system="SYS")
    assert not isinstance(action, UseItem)
