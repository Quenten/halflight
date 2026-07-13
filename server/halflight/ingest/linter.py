"""Vault linter — gate for M1.

Pure, side-effect-free validation of the Obsidian vault against the frontmatter
contracts in HANDOFF.md. `lint_vault` returns a report; the CLI prints it and
exits non-zero on any error. The engine/ingest layers assume a clean vault, so
this is the contract check that must pass before ingestion runs.

Checks (all ERROR unless noted):
- required frontmatter fields present per type
- id prefix matches type (loc_/npc_/fac_/itm_/lore_)
- unique ids across the whole vault
- no reserved-id collisions
- numeric ranges (danger 0-5, disposition -100..100, hp/value >= 0)
- enum fields (item.kind, npc.stats keys)
- no broken wikilinks or broken frontmatter relation references
- relation points at the wrong entity type (WARNING)
"""

from __future__ import annotations

import re
from collections.abc import Iterator
from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path
from typing import Any

import frontmatter

# Typed note folders, in walk order. Anything else (rules/, _templates/) is prose.
TYPED_DIRS = ("locations", "npcs", "factions", "items", "lore")

TYPE_PREFIX: dict[str, str] = {
    "location": "loc_",
    "npc": "npc_",
    "faction": "fac_",
    "item": "itm_",
    "lore": "lore_",
}

REQUIRED_FIELDS: dict[str, set[str]] = {
    "location": {"id", "type", "name", "district", "danger", "connections"},
    "npc": {"id", "type", "name", "role", "location", "disposition_default", "stats", "hp"},
    "faction": {"id", "type", "name"},
    "item": {"id", "type", "name", "kind", "value"},
    "lore": {"id", "type"},
}

STAT_KEYS = {"muscle", "nerve", "wits", "tech", "streetwise", "presence"}
ITEM_KINDS = {"weapon", "armor", "augment", "consumable", "key", "misc"}

# Ids the engine reserves for non-vault entities. A note may not claim these.
RESERVED_IDS = {"player", "world", "scene", "gm", "system", "none", "null", "self"}

# [[target]] or [[target|alias]] — target is captured, alias/anchor ignored.
_WIKILINK = re.compile(r"\[\[\s*([^\]|#]+?)\s*(?:#[^\]|]*)?(?:\|[^\]]*)?\]\]")


class Severity(StrEnum):
    ERROR = "error"
    WARNING = "warning"


@dataclass(frozen=True)
class Issue:
    severity: Severity
    file: str  # vault-relative path, forward slashes
    message: str

    def __str__(self) -> str:
        return f"{self.severity.value.upper():7} {self.file}: {self.message}"


@dataclass
class Note:
    id: str
    type: str
    file: str  # vault-relative
    meta: dict[str, Any]
    body: str


@dataclass
class LintReport:
    issues: list[Issue] = field(default_factory=list)
    notes: list[Note] = field(default_factory=list)

    @property
    def errors(self) -> list[Issue]:
        return [i for i in self.issues if i.severity is Severity.ERROR]

    @property
    def warnings(self) -> list[Issue]:
        return [i for i in self.issues if i.severity is Severity.WARNING]

    @property
    def ok(self) -> bool:
        return not self.errors


def _rel(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def _iter_relation_refs(note: Note) -> Iterator[tuple[str, set[str], str]]:
    """Yield (referenced_id, allowed_types, field_label) for frontmatter relations."""
    m = note.meta
    if note.type == "location":
        for lid in m.get("connections") or []:
            yield str(lid), {"location"}, "connections"
    elif note.type == "npc":
        fac = m.get("faction")
        if fac not in (None, "null", ""):
            yield str(fac), {"faction"}, "faction"
        loc = m.get("location")
        if loc:
            yield str(loc), {"location"}, "location"
        sched = m.get("schedule")
        if isinstance(sched, dict):
            for slot, lid in sched.items():
                if lid:
                    yield str(lid), {"location"}, f"schedule.{slot}"
    elif note.type == "faction":
        for r in m.get("rivals") or []:
            yield str(r), {"faction"}, "rivals"
        for a in m.get("allies") or []:
            yield str(a), {"faction"}, "allies"
        for t in m.get("territory") or []:
            yield str(t), {"location"}, "territory"


def _check_fields(note: Note) -> Iterator[Issue]:
    """Per-type required fields, prefixes, ranges, enums."""
    t = note.type

    def err(msg: str) -> Issue:
        return Issue(Severity.ERROR, note.file, msg)

    required = REQUIRED_FIELDS[t]
    for f in sorted(f for f in required if f not in note.meta or note.meta.get(f) is None):
        yield err(f"missing required field '{f}'")

    prefix = TYPE_PREFIX[t]
    if not note.id.startswith(prefix):
        yield err(f"id '{note.id}' must start with '{prefix}' for type '{t}'")
    if note.id in RESERVED_IDS:
        yield err(f"id '{note.id}' collides with a reserved engine id")
    if note.id != note.id.lower() or " " in note.id:
        yield err(f"id '{note.id}' must be lowercase snake_case")

    if t == "location":
        danger = note.meta.get("danger")
        if isinstance(danger, int) and not 0 <= danger <= 5:
            yield err(f"danger {danger} out of range 0-5")
    elif t == "npc":
        disp = note.meta.get("disposition_default")
        if isinstance(disp, int) and not -100 <= disp <= 100:
            yield err(f"disposition_default {disp} out of range -100..100")
        hp = note.meta.get("hp")
        if isinstance(hp, int) and hp <= 0:
            yield err(f"hp {hp} must be positive")
        stats = note.meta.get("stats")
        if isinstance(stats, dict):
            for s in sorted(STAT_KEYS - set(stats)):
                yield err(f"stats missing '{s}'")
            for s in sorted(set(stats) - STAT_KEYS):
                yield Issue(Severity.WARNING, note.file, f"stats has unknown key '{s}'")
        elif stats is not None:
            yield err("stats must be a mapping")
    elif t == "item":
        kind = note.meta.get("kind")
        if kind is not None and kind not in ITEM_KINDS:
            yield err(f"kind '{kind}' not in {sorted(ITEM_KINDS)}")
        value = note.meta.get("value")
        if isinstance(value, int) and value < 0:
            yield err(f"value {value} must be >= 0")


def lint_vault(vault_path: str | Path) -> LintReport:
    """Parse and validate a vault. Never raises on content problems — reports them."""
    root = Path(vault_path)
    report = LintReport()
    if not root.is_dir():
        report.issues.append(
            Issue(Severity.ERROR, str(vault_path), "vault path is not a directory")
        )
        return report

    # Pass 1: parse notes, per-note checks, build id index.
    by_id: dict[str, Note] = {}
    for sub in TYPED_DIRS:
        for path in sorted((root / sub).rglob("*.md")):
            rel = _rel(path, root)
            try:
                post = frontmatter.load(path)
            except Exception as exc:  # malformed YAML, etc.
                report.issues.append(
                    Issue(Severity.ERROR, rel, f"failed to parse frontmatter: {exc}")
                )
                continue
            meta: dict[str, Any] = dict(post.metadata)
            raw_type = meta.get("type")
            raw_id = meta.get("id")
            if not raw_type:
                report.issues.append(Issue(Severity.ERROR, rel, "missing 'type' in frontmatter"))
                continue
            note_type = str(raw_type)
            if note_type not in REQUIRED_FIELDS:
                report.issues.append(Issue(Severity.ERROR, rel, f"unknown type '{note_type}'"))
                continue
            if not raw_id:
                report.issues.append(Issue(Severity.ERROR, rel, "missing 'id' in frontmatter"))
                continue
            note_id = str(raw_id)
            note = Note(id=note_id, type=note_type, file=rel, meta=meta, body=str(post.content))
            report.notes.append(note)
            report.issues.extend(_check_fields(note))
            if note_id in by_id:
                other = by_id[note_id].file
                report.issues.append(
                    Issue(Severity.ERROR, rel, f"duplicate id '{note_id}' (also in {other})")
                )
            else:
                by_id[note_id] = note

    # Pass 2: cross-note references (needs the full id index).
    for note in report.notes:
        for ref, allowed, label in _iter_relation_refs(note):
            target = by_id.get(ref)
            if target is None:
                report.issues.append(
                    Issue(Severity.ERROR, note.file, f"{label} references unknown id '{ref}'")
                )
            elif target.type not in allowed:
                report.issues.append(
                    Issue(
                        Severity.WARNING,
                        note.file,
                        f"{label} '{ref}' is a {target.type}, expected {sorted(allowed)}",
                    )
                )
        for match in _WIKILINK.finditer(note.body):
            target_id = match.group(1).strip()
            if target_id not in by_id:
                report.issues.append(
                    Issue(Severity.ERROR, note.file, f"broken wikilink [[{target_id}]]")
                )

    return report


def _main(argv: list[str] | None = None) -> int:
    import sys

    args = argv if argv is not None else sys.argv[1:]
    vault = args[0] if args else "vault"
    report = lint_vault(vault)
    for issue in report.issues:
        print(issue, file=sys.stderr)
    summary = (
        f"lint: {len(report.notes)} notes, "
        f"{len(report.errors)} errors, {len(report.warnings)} warnings"
    )
    print(summary, file=sys.stderr)
    return 1 if report.errors else 0


if __name__ == "__main__":
    raise SystemExit(_main())
