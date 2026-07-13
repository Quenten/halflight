"""Turn receipt: TurnResult deltas -> plain {text, tone} items for the UI."""

from __future__ import annotations

from pathlib import Path

from halflight.engine.actions import Attack, Custom, Trade, UseItem
from halflight.engine.results import SceneEvent, StateChange, TurnResult
from halflight.gm.receipt import build_receipt
from halflight.ingest.runner import run_ingest
from sqlmodel import Session

from .conftest import FakeEmbedder

FIXTURE = Path(__file__).parent / "fixtures" / "vault_mini"


def _texts(items: list[dict[str, str]]) -> list[str]:
    return [i["text"] for i in items]


def test_empty_result_has_no_receipt(session: Session) -> None:
    res = TurnResult(action=Custom(description="wait"), valid=True, outcome="narrative_only")
    assert build_receipt(session, res, 1) == []


def test_roll_breakdown_chip(session: Session) -> None:
    res = TurnResult(
        action=Custom(description="pick the lock", stat_hint="tech"),
        valid=True, outcome="failure",
        roll=8, roll_base=6, roll_mod=2, difficulty=15,
    )
    items = build_receipt(session, res, 1)
    assert items[0]["text"] == "Roll 6 +2 = 8 vs 15"
    assert items[0]["tone"] == "bad"  # a failed check reads red


def test_combat_receipt(session: Session, fake_embedder: FakeEmbedder) -> None:
    run_ingest(FIXTURE, session, fake_embedder)
    res = TurnResult(
        action=Attack(target="npc_dax"),
        valid=True,
        outcome="success",
        state_changes=[
            StateChange(entity="npc_dax", field="hp", delta=-6),
            StateChange(entity="npc_dax", field="alive", delta=False),
            StateChange(entity="faction:fac_syndicate", field="rep", delta=-3),
            StateChange(entity="player", field="hp", delta=-4),
        ],
        scene_events=[
            SceneEvent(kind="npc_died", detail={"npc": "npc_dax"}),
            SceneEvent(kind="player_hit", detail={"by": "npc_dax", "damage": 4}),
        ],
    )
    items = build_receipt(session, res, 1)
    texts = _texts(items)
    assert "Dax took 6 damage" in texts
    assert "You took 4 damage" in texts
    assert "Dax killed" in texts
    assert any("standing -3" in t for t in texts)
    # tone is carried for colour
    assert {i["tone"] for i in items} <= {"good", "bad", "neutral"}
    assert next(i for i in items if i["text"] == "You took 4 damage")["tone"] == "bad"


def test_trade_and_item_receipt(session: Session, fake_embedder: FakeEmbedder) -> None:
    run_ingest(FIXTURE, session, fake_embedder)
    res = TurnResult(
        action=Trade(target="npc_dax", item="itm_shiv", direction="buy"),
        valid=True,
        outcome="success",
        state_changes=[
            StateChange(entity="player", field="credits", delta=-8),
            StateChange(entity="player", field="inventory:itm_shiv", delta=1),
        ],
        scene_events=[SceneEvent(kind="item_gained", detail={"item": "itm_shiv"})],
    )
    texts = _texts(build_receipt(session, res, 1))
    assert "Spent 8 scrip" in texts
    assert any(t.startswith("Picked up") for t in texts)


def test_heal_receipt(session: Session, fake_embedder: FakeEmbedder) -> None:
    run_ingest(FIXTURE, session, fake_embedder)
    res = TurnResult(
        action=UseItem(item="itm_stimshot"),
        valid=True,
        outcome="success",
        state_changes=[
            StateChange(entity="player", field="hp", delta=6),
            StateChange(entity="player", field="inventory:itm_stimshot", delta=-1),
        ],
        scene_events=[SceneEvent(kind="item_used", detail={"item": "itm_stimshot"})],
    )
    items = build_receipt(session, res, 1)
    texts = _texts(items)
    assert "Healed 6 HP" in texts
    assert any(t.startswith("Lost") for t in texts)
    assert next(i for i in items if i["text"] == "Healed 6 HP")["tone"] == "good"
