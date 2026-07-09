"""Chunker tests: heading splits, secret isolation, comment stripping, budget."""

from __future__ import annotations

from pathlib import Path

from halflight.ingest.chunker import approx_tokens, chunk_body
from halflight.ingest.linter import lint_vault

FIXTURE = Path(__file__).parent / "fixtures" / "vault_mini"


def _notes() -> dict[str, str]:
    return {n.id: n.body for n in lint_vault(FIXTURE).notes}


def test_secret_section_flagged() -> None:
    # loc_tram_hub: a preamble chunk (public) + a "## Secret" chunk (secret).
    chunks = chunk_body(_notes()["loc_tram_hub"])
    assert len(chunks) == 2
    assert chunks[0].is_secret is False
    assert chunks[1].is_secret is True
    assert "maintenance shaft" in chunks[1].text


def test_comment_only_body_yields_no_chunks() -> None:
    chunks = chunk_body("<!-- STUB: nothing to embed -->\n")
    assert chunks == []


def test_indices_are_sequential() -> None:
    chunks = chunk_body(_notes()["loc_tram_hub"])
    assert [c.chunk_ix for c in chunks] == list(range(len(chunks)))


def test_nested_secret_stays_secret() -> None:
    body = "Intro.\n\n## Secret\n\nHidden.\n\n### Deeper\n\nAlso hidden.\n"
    chunks = chunk_body(body)
    assert chunks[0].is_secret is False
    assert all(c.is_secret for c in chunks[1:])


def test_section_after_secret_is_public_again() -> None:
    body = "## Secret\n\nHidden.\n\n## Notes\n\nPublic again.\n"
    chunks = chunk_body(body)
    assert chunks[0].is_secret is True
    assert chunks[-1].is_secret is False
    assert "Public again" in chunks[-1].text


def test_large_section_splits_under_budget() -> None:
    para = "word " * 30  # ~150 chars ~37 tokens, each under the budget
    body = "## Big\n\n" + "\n\n".join([para] * 6) + "\n"
    chunks = chunk_body(body, max_tokens=100)
    assert len(chunks) >= 2
    # Packer emits before exceeding the budget; each chunk stays near it.
    assert all(approx_tokens(c.text) <= 130 for c in chunks)
