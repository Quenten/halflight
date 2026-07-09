# HALFLIGHT vault

Game canon. This is an Obsidian vault; open the `halflight/vault` folder as a vault.

**One-way rule:** the vault is authored by hand and ingested into Postgres. The
runtime never writes back here. Vault = canon, DB = what happened.

## Structure

- `_templates/` — copy these when authoring; skipped by the linter and ingestion
- `locations/` `npcs/` `factions/` `items/` `lore/` — typed notes (see templates)
- `rules/gm_style.md` — the narrator's voice (author writes this)

## Contracts

Each typed note needs frontmatter matching its template. Ids are permanent,
unique, lowercase snake_case, and prefixed by type: `loc_`, `npc_`, `fac_`,
`itm_`, `lore_`. Reserved ids (`player`, `world`, `scene`, ...) are off-limits.

Bodies are free markdown. `[[id]]` wikilinks define graph relationships; every
link must resolve. A `## Secret` section is hidden from retrieval until an engine
event reveals it.

## Lint

```powershell
uv run python -m halflight.ingest.linter vault
```

Exits non-zero on any error (broken links, duplicate/malformed ids, missing
fields, out-of-range values). Run it before ingesting. The seed target is 10
locations, 10 NPCs, 2 factions, 15 items, 5 lore notes.
