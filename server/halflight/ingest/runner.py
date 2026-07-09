"""Ingestion orchestrator: vault -> Postgres.

Lint is the gate: on any lint error nothing touches the DB. Otherwise each note's
typed row is upserted, its body chunked, and non-secret chunks embedded. A note is
skipped entirely when its content hash matches `note_index` (only changed notes are
re-embedded). Notes removed from the vault are deleted from the DB.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from sqlalchemy import delete as sa_delete
from sqlmodel import Session, SQLModel, col, select

from halflight.ingest.chunker import chunk_body
from halflight.ingest.embedder import Embedder
from halflight.ingest.linter import LintReport, lint_vault
from halflight.ingest.parser import note_hash, to_row
from halflight.models import Faction, Item, Location, LoreChunk, NoteIndex, Npc

# Typed tables keyed by note type (lore has no typed row).
_TYPE_MODEL: dict[str, type[SQLModel]] = {
    "faction": Faction,
    "location": Location,
    "item": Item,
    "npc": Npc,
}


@dataclass
class IngestReport:
    lint: LintReport
    notes_total: int = 0
    upserted: int = 0
    skipped: int = 0
    deleted: int = 0
    chunks_written: int = 0
    chunks_embedded: int = 0
    secret_chunks: int = 0
    aborted: bool = False
    messages: list[str] = field(default_factory=list)

    def summary(self) -> str:
        if self.aborted:
            return f"ingest aborted: {len(self.lint.errors)} lint error(s)"
        return (
            f"ingest: {self.notes_total} notes "
            f"({self.upserted} changed, {self.skipped} unchanged, {self.deleted} deleted), "
            f"{self.chunks_written} chunks ({self.chunks_embedded} embedded, "
            f"{self.secret_chunks} secret/held)"
        )


def _delete_note(session: Session, note_id: str, note_type: str) -> None:
    model = _TYPE_MODEL.get(note_type)
    if model is not None:
        row = session.get(model, note_id)
        if row is not None:
            session.delete(row)
    session.execute(sa_delete(LoreChunk).where(col(LoreChunk.source_note_id) == note_id))
    idx = session.get(NoteIndex, note_id)
    if idx is not None:
        session.delete(idx)


def run_ingest(vault: str | Path, session: Session, embedder: Embedder) -> IngestReport:
    lint = lint_vault(vault)
    report = IngestReport(lint=lint)
    if lint.errors:
        report.aborted = True
        return report

    notes_by_id = {n.id: n for n in lint.notes}
    report.notes_total = len(notes_by_id)

    # Deletion: note_index rows whose note is no longer in the vault.
    existing = {ni.id: ni for ni in session.exec(select(NoteIndex)).all()}
    for note_id, ni in existing.items():
        if note_id not in notes_by_id:
            _delete_note(session, note_id, ni.type)
            report.deleted += 1

    for note in lint.notes:
        h = note_hash(note.meta, note.body)
        prior = existing.get(note.id)
        if prior is not None and prior.body_hash == h:
            report.skipped += 1
            continue

        row = to_row(note)
        if row is not None:
            session.merge(row)

        # Changed/new: replace this note's chunks.
        session.execute(sa_delete(LoreChunk).where(col(LoreChunk.source_note_id) == note.id))
        chunks = chunk_body(note.body)

        embed_targets = [c for c in chunks if not c.is_secret]
        vectors = embedder.embed([c.text for c in embed_targets])
        vec_by_ix = {c.chunk_ix: v for c, v in zip(embed_targets, vectors, strict=True)}

        for c in chunks:
            session.add(
                LoreChunk(
                    source_note_id=note.id,
                    source_type=note.type,
                    chunk_ix=c.chunk_ix,
                    body=c.text,
                    embedding=vec_by_ix.get(c.chunk_ix),
                    is_secret=c.is_secret,
                    revealed=False,
                )
            )
            report.chunks_written += 1
            if c.is_secret:
                report.secret_chunks += 1
            else:
                report.chunks_embedded += 1

        session.merge(NoteIndex(id=note.id, type=note.type, body_hash=h))
        report.upserted += 1

    session.commit()
    return report
