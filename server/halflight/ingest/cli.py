"""`python -m halflight.ingest [vault_path]` — ingest the vault into Postgres."""

from __future__ import annotations

import sys

import httpx
from sqlmodel import Session

from halflight.config import get_settings
from halflight.db import engine
from halflight.ingest.embedder import LlamaEmbedder
from halflight.ingest.runner import run_ingest


def main(argv: list[str] | None = None) -> int:
    args = argv if argv is not None else sys.argv[1:]
    vault = args[0] if args else "vault"
    settings = get_settings()
    embedder = LlamaEmbedder(settings.llama_embed_url)

    with Session(engine) as session:
        try:
            report = run_ingest(vault, session, embedder)
        except httpx.HTTPError as exc:
            print(f"embedding server error at {settings.llama_embed_url}: {exc}", file=sys.stderr)
            print("is `llama-server --embedding` running? see README.", file=sys.stderr)
            return 3

    for issue in report.lint.issues:
        print(issue, file=sys.stderr)
    print(report.summary(), file=sys.stderr)
    return 2 if report.aborted else 0


if __name__ == "__main__":
    raise SystemExit(main())
