# THE CHRYSALIS — Worldbook Expansion v1

Extends WORLDBOOK.md. Same id conventions, same vault mapping approach.
Quests introduce a new entity type not yet in HANDOFF.md's data model —
see the note at the end before Claude Code builds the engine tables for it.

---

## LOCATIONS — expanded

Each district now has named sub-locations. Districts become hubs; sub-locations
are where scenes actually happen.

### Bridgeworks (loc_bridgeworks)
- **loc_charterhall** — the Charter Hall. Courtroom, law-reading, disputes settled
  in public. danger 1.
- **loc_wardenbarracks** — Warden barracks and armory. danger 1.
- **loc_observatory** — the one intact viewport gallery. Real light, real view of
  the Wastes. Where Directorate officials go to think, or to be seen thinking.
  danger 0.

### Upper Rings (loc_rings_upper)
- **loc_upperpromenade** — the nicer market strip. Real variety, real Directorate
  presence. danger 1.
- **loc_permitoffice** — Kess's office. Where Vaultwell access is requested,
  denied, or quietly arranged. danger 0.
- **loc_chapelrow** — a row of small Communion shrines tolerated by the
  Directorate for keeping the lower decks calm. danger 0.

### Lower Rings (loc_rings_lower)
- **loc_scrapmarket** — the real economy. Loud, dense, patched light, more
  Keelrat presence than Warden. danger 2.
- **loc_rustbucket** — Rook's home bar. Neutral ground, mostly. danger 1.
- **loc_underdeckflop** — a flophouse tenement, doors that don't lock, rent
  that's never fair. danger 2.
- **loc_checkpointseven** — a contested chokepoint between Directorate and
  Keelrat influence. Whoever's watching it changes week to week. danger 2.

### Vaultwell (loc_vaultwell)
- **loc_vaultshrine** — Lys's shrine at the main approach. danger 1.
- **loc_vaultannex** — overflow pod storage, poorly maintained, poorly lit.
  danger 2.
- **loc_frostgate** — the sealed inner gate to the deepest sleeper racks.
  Nobody gets past it without a reason the Wardens believe. danger 3.

### Engine Heart (loc_enginecore)
- **loc_reactorhall** — the reactor chamber itself. Heat, noise, danger 3.
- **loc_haleclinic** — Dr. Hale's augment clinic. danger 2.
- **loc_taplines** — the alley of illegal power taps. Nobody official comes
  down here. danger 3.

### Cargo Fathoms (loc_cargofathoms)
- **loc_floodedhold** — the lower hold, ankle-to-knee deep in runoff that was
  never meant to pool. danger 3.
- **loc_smugglersrun** — a service tunnel repurposed for moving things that
  shouldn't move. danger 3.
- **loc_drydockseven** — an old cargo dock now a Keelrat stash house. danger 3.

### Deep Hull (loc_deephull) — post-MVP
- **loc_collapsedspine** — the central corridor, half-collapsed, still settling.
  danger 4.
- **loc_ghostlab** — an abandoned science bay. Equipment still humming that
  shouldn't have power. danger 5.
- **loc_thecradle** — the deepest, strangest chamber anyone's mapped. What it
  is remains a mystery for the owner to decide. danger 5.

### Wastesgate (loc_wastesgate)
- **loc_outerwastes** — the dust flat just outside the gate. danger 2.
- **loc_relaytower** — a dead relay tower visible from the gate, unreached.
  danger 3.

**Total: ~7 district hubs + 20 sub-locations = 27 named locations.**

---

## ITEMS — 50 total

### Weapons (12)

| id | name | value | notes |
|---|---|---|---|
| itm_charter_sidearm | Charter Sidearm | 300 | Directorate-issue, requires visible permit |
| itm_wardenrifle | Warden Rifle | 550 | Restricted, better accuracy, Warden armory only |
| itm_slugpipe | Slugpipe | 40 | Homemade, unreliable, everywhere below the Rings |
| itm_keelblade | Keelblade | 90 | Common Keelrat sidearm/melee |
| itm_scraphammer | Scrap Hammer | 60 | Improvised heavy melee |
| itm_stunbaton | Stun Baton | 200 | Warden nonlethal crowd control |
| itm_saltgun | Salt Gun | 250 | Fires corrosive coolant-salt rounds; ammo scavengeable from ship systems |
| itm_harpoon | Deep Harpoon | 180 | Boarding harpoon, favored in the Fathoms |
| itm_derringer | Smuggler's Derringer | 150 | Small, concealable, low damage |
| itm_ratpick | Ratpick | 70 | Icepick-style enforcer weapon |
| itm_relic_sidearm | Relic Sidearm | 900 | Pristine pre-Fall officer's weapon. Rare, prestigious, a target for theft |
| itm_riotshield | Riot Shield | 220 | Warden defensive gear, reduces incoming damage, slows movement |

### Augments (8)

| id | name | value | notes |
|---|---|---|---|
| itm_medbay_graft | Medbay Graft | 400 | Generic salvaged nanotech augment |
| itm_ocular_relay | Ocular Relay | 500 | Low-light vision, eye augment |
| itm_dermal_plate | Dermal Plate | 600 | Subdermal armor plating |
| itm_neural_dampener | Neural Dampener | 350 | Blunts pain/fear response; addictive with extended use |
| itm_reflex_splice | Reflex Splice | 700 | Nerve splice, faster reactions |
| itm_voxbox | Voxbox | 1200 | Rare vocal augment tuned to STEWARD frequencies. Communion prizes these highly |
| itm_grip_servos | Grip Servos | 300 | Muscle augment, carrying/melee bonus |
| itm_filtration_lung | Filtration Lung | 650 | Internal augment; removes need for a mask in low-danger hazard zones |

### Consumables (10)

| id | name | value | notes |
|---|---|---|---|
| itm_cryovial | Cryovial | 500 | Stabilized cryo-fluid; legitimate thaws or illegal early-thaws |
| itm_stimpatch | Stim Patch | 30 | Basic healing item |
| itm_rationbar | Ration Bar | 5 | Basic food |
| itm_rustgin | Rust Gin | 15 | Keelrat home brew, social/morale item |
| itm_filteredwater | Filtered Water | 10 | Clean water ration |
| itm_painkillers | Painkillers | 45 | Black-market medical item |
| itm_coolantdraft | Coolant Draft | 60 | Dangerous drug made from reactor coolant; Enginecore specific |
| itm_antirad | Antirad | 80 | Anti-radiation medicine, needed for extended Enginecore/Deep Hull time |
| itm_sleepmoss | Sleepmoss | 25 | Sedative fungus found in the Fathoms |
| itm_stewardstatic | Steward Static | 150 | Cult substance said to let you "hear" STEWARD more clearly. Risky. |

### Keys (8)

| id | name | notes |
|---|---|---|
| itm_access_chit | Access Chit | Restricted-deck permit, especially Vaultwell |
| itm_steward_relic | Steward Relic | Pre-Fall tech fragment, STEWARD's old core-language |
| itm_wardenbadge | Warden Badge | Grants authority/access if not recognized as stolen |
| itm_reactorkey | Reactor Key | Physical key to restricted Enginecore systems |
| itm_frostgateseal | Frostgate Seal | Needed to open the Frostgate in the Vaultwell |
| itm_charterseal | Charter Seal | Official Directorate document seal; forgery/legitimacy hook |
| itm_deephullbeacon | Deep Hull Beacon | Left behind by missing Deep Crew members |
| itm_manifestledger | Manifest Ledger | Stolen Keelrat debt records; blackmail material |

### Misc (12)

| id | name | notes |
|---|---|---|
| itm_o2mask | Filtration Mask | Required for extended Fathoms/Deep Hull time |
| itm_toolkit | Toolkit | Engineering tool set, tech checks |
| itm_lockpicks | Lockpicks | Lockpicking set |
| itm_flare | Flare | Emergency light/signal |
| itm_ropecoil | Rope Coil | Climbing/utility rope |
| itm_radsuit | Rad Suit | Hazard suit for reactor/Deep Hull exposure |
| itm_datachip | Blank Datachip | For copying data |
| itm_oldphoto | Old Photograph | Pre-Fall photo. No mechanical effect — pure flavor/quest item |
| itm_ledgercopy | Charter Ledger Copy | Copied Directorate financial records; blackmail material |
| itm_stewardhymn | Steward Hymn | Written transcription of STEWARD fragments; Communion text |
| itm_scrapbundle | Scrap Metal Bundle | Raw crafting/repair material |
| itm_filtercartridge | Filter Cartridge | Replacement part for filtration systems |

**Note:** `augment` should be added as a formal item `kind` alongside
weapon/consumable/key/misc in the engine's item schema.

---

## NPCS — 25 total

Building on the 9 already established (Orsa, Kess, Rook, Bosun Grey, Hale, Lys,
Teller, Ferro, Vask) plus the STEWARD fragment entity. 16 new below.

### Directorate
- **npc_hollis** — Warden Hollis. Young, idealistic, serves under Orsa. Starting
  to notice the gap between Charter law and Charter justice. Good hook for a
  "conscience" storyline. loc_wardenbarracks.
- **npc_vahl** — Director Vahl. Senior Directorate official, political rival to
  Kess's superiors, aristocratic bearing, plays the long game. loc_bridgeworks.
- **npc_pell** — Archivist Pell. Keeper of the old logs — the ones that hint
  STEWARD grounded the ship on purpose. Knows more than the Directorate wants
  known. loc_charterhall.

### Keelrats
- **npc_mira** — Scrap Queen Mira. Rival fixer to Rook, tighter margins, less
  charm, more fear. loc_scrapmarket.
- **npc_theledger** — "The Ledger." Keelrat accountant, tracks every debt on the
  Husk, ruthless, faction-neutral in practice — everyone owes them something.
  loc_drydockseven.
- **npc_switch** — Switch. Young runner/smuggler, fast, cocky, useful for
  courier-type work. loc_scrapmarket.
- **npc_dredge** — Dredge. Enforcer who works the flooded holds. Taciturn,
  physically imposing, prefers the harpoon. loc_floodedhold.

### Communion
- **npc_orin** — High Shepherd Orin. Head of the Communion, more political than
  Lys, genuine believer with an agenda. loc_chapelrow.
- **npc_neve** — Acolyte Neve. Young initiate, starting to doubt the official
  story of the Long Fall. Personal-crisis quest hook. loc_vaultshrine.
- **npc_theunheard** — "The Unheard." A Communion heretic who believes STEWARD
  should be destroyed, not worshipped — its guilt-driven fragments are cruelty,
  not care. loc_chapelrow (fringe presence).

### Wakeful (post-MVP)
- **npc_ilsa** — Thaw Medic Ilsa. Handles the Wakeful's illegal early-thaw
  attempts. Skilled, morally torn, has lost patients. loc_underdeckflop.
- **npc_bahn** — Recorder Bahn. Documents Wakeful "martyrs," radicalizing
  propagandist, believes in the cause more than the people in it.
  loc_rings_lower.

### Deep Crew (post-MVP)
- **npc_soo** — Cartographer Soo. Maps the Deep Hull, quiet, meticulous, the
  reason Deep Crew salvage runs don't get everyone killed. loc_cargofathoms.
- **npc_arn** — "Lostboy" Arn. A Deep Crew scout who came back from the Deep
  Hull wrong — alive, coherent, but not quite right. Unsettling. Good horror
  hook for loc_deephull content. loc_cargofathoms.

### Neutral / Wastes
- **npc_teller** — (existing) A sleeper thawed early by accident decades ago.
- **npc_kade** — Outrider Kade. Wastes scavenger, trades salvage at the gate,
  one of very few who regularly goes outside and comes back. loc_wastesgate.
- **npc_firstwaker** — "First Waker." A very recently, accidentally-thawed
  sleeper who has no memory of ever having lived before the ice. Fully
  dependent, deeply unsettling to talk to, a living symbol of what the
  Wakeful are fighting for and what the Directorate is afraid of.
  loc_vaultannex.

---

## QUESTS — 5 seed quests

Quests are a new entity type — not yet in HANDOFF.md's data model. Proposed
frontmatter and engine addition below, then the five quests.

### Proposed schema

```yaml
---
id: qst_<slug>
type: quest
name: <display name>
giver: npc_<id>            # or null for environmental/discovered quests
factions: [fac_x]          # factions with a stake, for rep effects
locations: [loc_x, loc_y]  # where it plays out
stages: [stage_slug, ...]  # ordered; engine tracks current stage per run
repeatable: false
---
Body: narrative summary, stage-by-stage notes, branching outcomes,
reward table (credits, items, faction rep deltas per outcome).
```

**Engine addition needed:** a `quests` table (from ingestion, mirrors NPCs/
locations) plus a per-run `quest_states(run_id, quest_id, current_stage,
status: not_started|active|complete|failed)` table. Stage transitions are
triggered by `scene_events` from the engine (same mechanism as NPC memory) —
a quest is really just a named, tracked pattern of events. Discuss with
Claude Code during M3 how to hook stage-completion checks into `TurnResult`
without letting the LLM decide quest progression itself.

### qst_permit_for_ice
**Giver:** npc_rook. **Factions:** fac_directorate, fac_keelrats.
**Locations:** loc_permitoffice, loc_scrapmarket, loc_vaultwell.

Rook needs a Vaultwell access chit for a client who won't say why. Kess can be
bribed, blackmailed (if the player finds leverage), or the chit can simply be
stolen off a Warden. Each path changes who ends up owing whom. Ends with the
player deciding whether to actually deliver the chit to Rook's client — and
finding out, if they push, why the client wanted in.

### qst_the_ledger_debt
**Giver:** npc_switch (on behalf of npc_mira). **Factions:** fac_keelrats.
**Locations:** loc_drydockseven, loc_scrapmarket.

Mira wants The Ledger's actual debt records — leverage over half the Lower
Rings. A heist-or-negotiate quest: steal the manifest_ledger outright, or
find out what The Ledger actually wants and broker a trade. Handing it to
Mira versus keeping it yourself versus returning it to The Ledger are three
different endings with different long-term rep consequences.

### qst_shepherds_doubt
**Giver:** npc_neve. **Factions:** fac_communion, fac_directorate.
**Locations:** loc_vaultshrine, loc_charterhall, loc_bridgeworks.

Neve wants to know if the Long Fall really was STEWARD's sacrifice, or a
cover-up for a Directorate ancestor's failure. Archivist Pell has the old
logs. Lys warns against digging. High Shepherd Orin has his own reasons to
want a specific answer to win. The steward_relic item is the physical proof,
whatever it turns out to prove.

### qst_first_thaw
**Giver:** npc_ilsa. **Factions:** fac_wakeful, fac_directorate.
**Locations:** loc_underdeckflop, loc_vaultannex.

The Wakeful are attempting an illegal early thaw using a stolen cryovial.
The player can help it succeed, sabotage it, or report it to the Directorate
for a reward. If it succeeds, npc_firstwaker is the direct result — giving
this quest a living consequence that persists in the world afterward rather
than just a stat/rep payout.

### qst_into_the_deep
**Giver:** npc_ferro. **Factions:** fac_deepcrew. **Locations:**
loc_cargofathoms, loc_deephull (loc_collapsedspine, loc_ghostlab).

Ferro's crew went into the Deep Hull and didn't fully come back — Arn did,
wrong. Using the deephull_beacon, the player can track what happened.
Salvage-run structure with escalating danger (danger 3 → 4 → 5 across the
three Deep Hull sub-locations) and a genuinely open question at the end about
what's actually down there. Best positioned as late-game / post-MVP content
alongside loc_deephull and fac_wakeful.

---

## Suggested build order for this expansion

1. Finish MVP scope from WORLDBOOK.md first if not already done (7 hub
   locations, 7 MVP NPCs, ~15 MVP items, 3 MVP factions).
2. Add sub-locations and the remaining items/NPCs from this file in one
   ingestion pass — they're all flagged by faction/location so nothing here
   should orphan.
3. Build qst_permit_for_ice first — it only touches MVP entities (Rook, Kess,
   Directorate, Keelrats) and is the best testbed for the quest_states engine
   addition before you commit to the schema for the other four.
4. Hold qst_first_thaw and qst_into_the_deep until fac_wakeful, fac_deepcrew,
   and loc_deephull exist (Milestone 7 territory per HANDOFF.md).
