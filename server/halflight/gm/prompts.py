"""Load the author-written prompt assets from vault/rules/.

These are the game's voice and rules (gm_style, narrator_rules, few-shot
examples, parser prompt). Cached — they change rarely and are reloaded on restart.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path


@lru_cache(maxsize=32)
def load_rule(vault_path: str, name: str) -> str:
    return (Path(vault_path) / "rules" / name).read_text(encoding="utf-8")


def gm_style(vault_path: str) -> str:
    return load_rule(vault_path, "gm_style.md")


def narrator_rules(vault_path: str) -> str:
    return load_rule(vault_path, "narrator_rules.md")


def narration_examples(vault_path: str) -> str:
    return load_rule(vault_path, "narration_examples.md")


def parser_prompt(vault_path: str) -> str:
    return load_rule(vault_path, "parser_prompt.md")
