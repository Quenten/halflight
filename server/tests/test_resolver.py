"""Resolver unit tests. Scripted rolls make combat deterministic."""

from __future__ import annotations

from halflight.engine.actions import Attack, Custom, Move, Talk, Trade, UseItem
from halflight.engine.gamestate import GameState, ItemView, LocationView, NpcView, PlayerView
from halflight.engine.resolver import resolve


class SeqRoller:
    """Returns scripted d20 values in order."""

    def __init__(self, values: list[int]) -> None:
        self._v = list(values)

    def d20(self) -> int:
        return self._v.pop(0)


def make_state(*, player_hp: int = 20, credits: int = 0) -> GameState:
    return GameState(
        player=PlayerView(
            hp=player_hp,
            location_id="loc_a",
            stats={},
            inventory={"itm_medkit": 1},
            credits=credits,
        ),
        location=LocationView(id="loc_a", connections=["loc_b"]),
        npcs={
            "npc_thug": NpcView(id="npc_thug", hp=20, stats={}, location_id="loc_a"),
            "npc_corpse": NpcView(
                id="npc_corpse", hp=0, stats={}, location_id="loc_a", alive=False
            ),
        },
        items={
            "itm_shiv": ItemView(id="itm_shiv", kind="weapon", value=50, effects={"damage": 4}),
            "itm_medkit": ItemView(id="itm_medkit", kind="consumable", effects={"heal": 5}),
        },
    )


def test_move_valid_and_invalid() -> None:
    ok = resolve(make_state(), Move(target="loc_b"), SeqRoller([]))
    assert ok.valid and ok.outcome == "success"
    assert any(c.field == "location_id" and c.delta == "loc_b" for c in ok.state_changes)

    bad = resolve(make_state(), Move(target="loc_z"), SeqRoller([]))
    assert not bad.valid and bad.outcome == "invalid"


def test_talk_present_and_dead() -> None:
    ok = resolve(make_state(), Talk(target="npc_thug", topic="the docks"), SeqRoller([]))
    assert ok.outcome == "narrative_only"
    dead = resolve(make_state(), Talk(target="npc_corpse"), SeqRoller([]))
    assert not dead.valid and dead.outcome == "invalid"


def test_attack_kills_in_one_hit() -> None:
    state = make_state()
    state.npcs["npc_thug"].hp = 3
    res = resolve(state, Attack(target="npc_thug", method="itm_shiv"), SeqRoller([20]))
    assert res.outcome == "success"
    assert any(e.kind == "npc_died" for e in res.scene_events)
    assert any(c.entity == "npc_thug" and c.field == "alive" and c.delta is False
               for c in res.state_changes)
    assert res.significance == 2


def test_attack_miss_then_lethal_retaliation() -> None:
    state = make_state(player_hp=3)
    res = resolve(state, Attack(target="npc_thug"), SeqRoller([1, 20]))  # miss, then npc crit
    assert res.outcome == "failure"
    assert any(e.kind == "player_died" for e in res.scene_events)
    assert res.significance == 3
    assert any(c.entity == "player" and c.field == "hp" and c.delta < 0 for c in res.state_changes)


def test_attack_absent_target_invalid() -> None:
    res = resolve(make_state(), Attack(target="npc_ghost"), SeqRoller([20]))
    assert not res.valid and res.outcome == "invalid"


def test_trade_buy_insufficient_and_success() -> None:
    poor = resolve(
        make_state(credits=10), Trade(target="npc_thug", item="itm_shiv", direction="buy"),
        SeqRoller([]),
    )
    assert poor.outcome == "failure" and poor.valid

    rich = resolve(
        make_state(credits=100), Trade(target="npc_thug", item="itm_shiv", direction="buy"),
        SeqRoller([]),
    )
    assert rich.outcome == "success"
    assert any(c.field == "credits" and c.delta == -50 for c in rich.state_changes)
    assert any(c.field == "inventory:itm_shiv" and c.delta == 1 for c in rich.state_changes)


def test_use_item_heals_and_consumes() -> None:
    res = resolve(make_state(), UseItem(item="itm_medkit"), SeqRoller([]))
    assert res.outcome == "success"
    assert any(c.field == "hp" and c.delta == 5 for c in res.state_changes)
    assert any(c.field == "inventory:itm_medkit" and c.delta == -1 for c in res.state_changes)


def test_custom_impossible_has_no_effect() -> None:
    res = resolve(
        make_state(), Custom(description="I find 500 scrip on the ground"), SeqRoller([])
    )
    assert res.outcome == "failure"
    assert res.state_changes == []
    assert any(e.kind == "no_effect" for e in res.scene_events)


def test_custom_impossible_without_leading_pronoun() -> None:
    # The parser often drops "I"; fiat acquisition must still be caught.
    for desc in ("find 5000 scrip on the floor and pocket it", "grab a gun from the shelf"):
        res = resolve(make_state(), Custom(description=desc), SeqRoller([]))
        assert res.outcome == "failure", desc
        assert res.state_changes == []


def test_custom_plausible_success() -> None:
    res = resolve(
        make_state(), Custom(description="pry open the vent", stat_hint="tech"), SeqRoller([20])
    )
    assert res.outcome == "success"
    assert res.difficulty == 15
