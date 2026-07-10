"""FastAPI application entry point."""

from __future__ import annotations

from fastapi import FastAPI

from halflight.api import admin, runs, turn

app = FastAPI(title="HALFLIGHT", version="0.1.0")

app.include_router(runs.router)
app.include_router(turn.router)
app.include_router(admin.router)


@app.get("/healthz")
def healthz() -> dict[str, str]:
    return {"status": "ok"}
