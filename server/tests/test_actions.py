"""Action schema: discriminated parse + TurnResult round-trip."""

from __future__ import annotations

import pytest
from halflight.engine.actions import Attack, Custom, Move, parse_action
from halflight.engine.results import TurnResult
from pydantic import ValidationError


def test_parse_discriminates_on_kind() -> None:
    assert isinstance(parse_action({"kind": "move", "target": "loc_x"}), Move)
    atk = parse_action({"kind": "attack", "target": "npc_x", "method": "shiv"})
    assert isinstance(atk, Attack) and atk.method == "shiv"


def test_custom_stat_hint_validated() -> None:
    c = parse_action({"kind": "custom", "description": "climb the gantry", "stat_hint": "muscle"})
    assert isinstance(c, Custom) and c.stat_hint == "muscle"
    with pytest.raises(ValidationError):
        parse_action({"kind": "custom", "description": "x", "stat_hint": "luck"})


def test_unknown_kind_rejected() -> None:
    with pytest.raises(ValidationError):
        parse_action({"kind": "teleport", "target": "loc_x"})


def test_trade_requires_direction() -> None:
    with pytest.raises(ValidationError):
        parse_action({"kind": "trade", "target": "npc_x", "item": "itm_y"})


def test_turnresult_roundtrip_preserves_action() -> None:
    tr = TurnResult(
        action=Move(target="loc_underlevel"),
        valid=True,
        outcome="success",
    )
    dumped = tr.model_dump()
    assert dumped["action"]["kind"] == "move"
    restored = TurnResult.model_validate(dumped)
    assert isinstance(restored.action, Move)
    assert restored.action.target == "loc_underlevel"
