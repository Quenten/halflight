"""FastAPI application entry point."""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse

from halflight.api import admin, runs, turn

_WEB = Path(__file__).resolve().parents[2] / "web"

app = FastAPI(title="HALFLIGHT", version="0.1.0")

app.include_router(runs.router)
app.include_router(turn.router)
app.include_router(admin.router)


@app.get("/healthz")
def healthz() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/")
def index() -> FileResponse:
    return FileResponse(_WEB / "index.html")
