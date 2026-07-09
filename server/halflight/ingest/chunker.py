"""Split a note body into retrieval chunks.

Chunking respects markdown headings and keeps chunks near a token budget.
Sections under a `## Secret` heading (any level) are flagged is_secret so
ingestion can store them unembedded until an engine event reveals them.
HTML comments are stripped, so stub/template bodies produce no chunks.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

MAX_TOKENS = 300

_HEADING = re.compile(r"^(#{1,6})\s+(.*?)\s*$")
_HTML_COMMENT = re.compile(r"<!--.*?-->", re.DOTALL)
_PARA_SPLIT = re.compile(r"\n\s*\n")


@dataclass
class Chunk:
    chunk_ix: int
    text: str
    is_secret: bool


def approx_tokens(text: str) -> int:
    """Rough token estimate (~4 chars/token). Good enough for sizing chunks."""
    return max(1, len(text) // 4)


@dataclass
class _Section:
    title: str | None
    lines: list[str]
    is_secret: bool


def _split_sections(body: str) -> list[_Section]:
    sections: list[_Section] = []
    current = _Section(title=None, lines=[], is_secret=False)
    secret_from_level: int | None = None

    for line in body.splitlines():
        m = _HEADING.match(line)
        if not m:
            current.lines.append(line)
            continue
        sections.append(current)
        level = len(m.group(1))
        title = m.group(2).strip()
        if secret_from_level is not None and level <= secret_from_level:
            secret_from_level = None
        is_secret = secret_from_level is not None
        if title.lower() == "secret":
            secret_from_level = level
            is_secret = True
        current = _Section(title=title, lines=[line], is_secret=is_secret)

    sections.append(current)
    return sections


def _pack(text: str, max_tokens: int) -> list[str]:
    """Greedily pack paragraphs into chunks under the token budget."""
    if approx_tokens(text) <= max_tokens:
        return [text]
    chunks: list[str] = []
    buf = ""
    for para in _PARA_SPLIT.split(text):
        para = para.strip()
        if not para:
            continue
        candidate = f"{buf}\n\n{para}" if buf else para
        if buf and approx_tokens(candidate) > max_tokens:
            chunks.append(buf)
            buf = para
        else:
            buf = candidate
    if buf:
        chunks.append(buf)
    return chunks


def chunk_body(body: str, max_tokens: int = MAX_TOKENS) -> list[Chunk]:
    body = _HTML_COMMENT.sub("", body)
    chunks: list[Chunk] = []
    ix = 0
    for sec in _split_sections(body):
        # Skip sections with no content beyond their heading.
        content = sec.lines[1:] if sec.title is not None else sec.lines
        if not "".join(content).strip():
            continue
        text = "\n".join(sec.lines).strip()
        for part in _pack(text, max_tokens):
            part = part.strip()
            if part:
                chunks.append(Chunk(chunk_ix=ix, text=part, is_secret=sec.is_secret))
                ix += 1
    return chunks
