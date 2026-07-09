"""Linter tests: the valid fixture passes; each error class is caught."""

from __future__ import annotations

import shutil
from pathlib import Path

from halflight.ingest.linter import Severity, lint_vault

FIXTURE = Path(__file__).parent / "fixtures" / "vault_mini"


def _messages(vault: Path) -> list[str]:
    return [i.message for i in lint_vault(vault).issues]


def test_valid_vault_passes() -> None:
    report = lint_vault(FIXTURE)
    assert report.ok, [str(i) for i in report.errors]
    assert not report.warnings, [str(i) for i in report.warnings]
    assert len(report.notes) == 7


def test_missing_dir_is_error() -> None:
    report = lint_vault(FIXTURE / "does_not_exist")
    assert not report.ok


def _copy(vault: Path, tmp_path: Path) -> Path:
    dst = tmp_path / "vault"
    shutil.copytree(vault, dst)
    return dst


def test_broken_wikilink(tmp_path: Path) -> None:
    vault = _copy(FIXTURE, tmp_path)
    note = vault / "locations" / "loc_tram_hub.md"
    note.write_text(note.read_text(encoding="utf-8") + "\nSee [[npc_ghost]].\n", encoding="utf-8")
    report = lint_vault(vault)
    assert not report.ok
    assert any("broken wikilink [[npc_ghost]]" in m for m in _messages(vault))


def test_duplicate_id(tmp_path: Path) -> None:
    vault = _copy(FIXTURE, tmp_path)
    src = (vault / "items" / "itm_shiv.md").read_text(encoding="utf-8")
    (vault / "items" / "itm_shiv_copy.md").write_text(src, encoding="utf-8")
    report = lint_vault(vault)
    assert any("duplicate id 'itm_shiv'" in i.message for i in report.errors)


def test_missing_required_field(tmp_path: Path) -> None:
    vault = _copy(FIXTURE, tmp_path)
    note = vault / "locations" / "loc_underlevel.md"
    text = note.read_text(encoding="utf-8").replace("district: spindle\n", "")
    note.write_text(text, encoding="utf-8")
    report = lint_vault(vault)
    assert any("missing required field 'district'" in i.message for i in report.errors)


def test_reserved_id(tmp_path: Path) -> None:
    vault = _copy(FIXTURE, tmp_path)
    (vault / "locations" / "player.md").write_text(
        "---\nid: player\ntype: location\nname: X\ndistrict: d\ndanger: 0\nconnections: []\n---\n",
        encoding="utf-8",
    )
    report = lint_vault(vault)
    assert any("reserved engine id" in i.message for i in report.errors)


def test_bad_prefix(tmp_path: Path) -> None:
    vault = _copy(FIXTURE, tmp_path)
    (vault / "items" / "bad.md").write_text(
        "---\nid: loc_wrong\ntype: item\nname: X\nkind: misc\nvalue: 1\n---\n",
        encoding="utf-8",
    )
    report = lint_vault(vault)
    assert any("must start with 'itm_'" in i.message for i in report.errors)


def test_danger_out_of_range(tmp_path: Path) -> None:
    vault = _copy(FIXTURE, tmp_path)
    note = vault / "locations" / "loc_tram_hub.md"
    text = note.read_text(encoding="utf-8").replace("danger: 1", "danger: 9")
    note.write_text(text, encoding="utf-8")
    report = lint_vault(vault)
    assert any("danger 9 out of range" in i.message for i in report.errors)


def test_bad_item_kind(tmp_path: Path) -> None:
    vault = _copy(FIXTURE, tmp_path)
    note = vault / "items" / "itm_shiv.md"
    text = note.read_text(encoding="utf-8").replace("kind: weapon", "kind: laser")
    note.write_text(text, encoding="utf-8")
    report = lint_vault(vault)
    assert any("kind 'laser' not in" in i.message for i in report.errors)


def test_missing_stat_key(tmp_path: Path) -> None:
    vault = _copy(FIXTURE, tmp_path)
    note = vault / "npcs" / "npc_vera.md"
    text = note.read_text(encoding="utf-8").replace("muscle: 10, ", "")
    note.write_text(text, encoding="utf-8")
    report = lint_vault(vault)
    assert any("stats missing 'muscle'" in i.message for i in report.errors)


def test_wrong_relation_type_is_warning(tmp_path: Path) -> None:
    vault = _copy(FIXTURE, tmp_path)
    # Point npc_dax.faction at a location id -> exists but wrong type -> warning, not error.
    note = vault / "npcs" / "npc_dax.md"
    text = note.read_text(encoding="utf-8").replace(
        "faction: fac_syndicate", "faction: loc_tram_hub"
    )
    note.write_text(text, encoding="utf-8")
    report = lint_vault(vault)
    assert report.ok  # only a warning
    assert any(i.severity is Severity.WARNING and "faction" in i.message for i in report.issues)
