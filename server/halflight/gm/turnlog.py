"""Persist every prompt+completion pair to disk — the future fine-tuning dataset.

One JSON file per turn at logs/turns/{run_id}/{turn_no}.json.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from halflight.models.runtime import utcnow


def log_turn(
    logs_dir: str | Path,
    run_id: int,
    turn_no: int,
    *,
    player_text: str,
    parse_prompt: str,
    parse_output: str,
    narration_context: str,
    narration: str,
    action: dict[str, Any],
    result: dict[str, Any],
) -> Path:
    out_dir = Path(logs_dir) / "turns" / str(run_id)
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"{turn_no}.json"
    payload = {
        "run_id": run_id,
        "turn_no": turn_no,
        "ts": utcnow().isoformat(),
        "player_text": player_text,
        "parse": {"prompt": parse_prompt, "output": parse_output},
        "action": action,
        "result": result,
        "narration": {"context": narration_context, "text": narration},
    }
    path.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    return path
