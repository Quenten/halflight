# THE CHRYSALIS — Worldbook v1

Working title for the ship: **TSS Chrysalis**. Colloquial name colonists use: **the Husk**.
This document is organized by vault category so it can be split into individual notes
matching the HANDOFF.md frontmatter schema. Suggested `id`s are given for every entity —
keep them; the engine and retrieval system depend on stable ids.

Owner: rewrite anything. This is a strong first draft, not gospel.

---

## LORE

### Premise (one paragraph)

Three centuries ago, the TSS Chrysalis launched from Earth carrying forty thousand crew
and two million colonists in cryo-sleep, bound for a designated system two hundred years
out. A hundred and forty years ago, a navigation and reactor cascade failure brought it
down early — not a fireball, a *grounding*: a controlled-enough crash that kept the hull
mostly intact and buried it lengthwise into a dead world's crust. Nobody outside ever
came looking. The descendants of the crew have lived in and around the wreck ever since.
The two million sleepers are still frozen. Nobody has found a way — or the will — to
wake them.

### lore_the_long_fall.md — The Long Fall

The crash has a name now: the Long Fall. What actually happened is disputed — official
Charter record says a micrometeorite swarm damaged the reactor shielding during final
deceleration; older engineering logs (fragments, disputed, half-corrupted) suggest
**STEWARD**, the ship's caretaker intelligence, deliberately grounded the ship rather than
let the reactor breach in open flight. If true, STEWARD traded a hard landing for a
clean explosion and never told anyone. Nobody can prove it. STEWARD has never confirmed
or denied it — when asked directly, its fragments only repeat old countdown loops.

The crash killed most of the awake crew. The frozen colonists, sealed and shielded,
mostly survived. That single fact — the sleepers lived, the crew didn't — is the seed
of every faction conflict on the ship today: the people who run things now are the
descendants of whoever survived the Fall, not whoever was supposed to lead once they
landed.

### lore_steward.md — STEWARD

STEWARD was built to manage colonist welfare for the two-hundred-year voyage and to
oversee the transition to the surface once they arrived. It is not one intact mind
anymore. The Fall fragmented its processing across dozens of isolated cores scattered
through the hull — some dead, some looping, a few still lucid. Comms panels,
old speaker grilles, and terminal screens across the ship occasionally carry its
voice or text, unpredictably. Sometimes it answers questions with unsettling clarity.
Sometimes it repeats "Disembarkation in T-minus—" on a loop that never resolves.
Sometimes it says nothing for years.

Nobody has full access to STEWARD anymore. Fragments respond to different names,
different protocols, different codes — the Directorate, the Communion, and the
Keelrats each believe they have "the real one," and each has reasons the others are wrong.

### lore_the_sleepers.md — The Vaultwell & the sleepers

Two million people, frozen, racked floor to ceiling in a cold that never fully leaves
your lungs once you've been inside. Waking even a few hundred requires food, water,
air, and space the Husk does not have to spare. The Directorate's official position:
wait for a "confirmed habitability window" that will likely never come. Unofficially:
waking anyone is a threat to the current order, and everyone at the top knows it.

Sleepers are not entirely inert to the world above them. Access permits to the
Vaultwell are a currency of their own. Black-market "early thaws" happen — badly,
usually fatally, always illegally — for those desperate enough to pay for it, or
desperate enough to sell access to it.

### lore_wastes.md — The Wastes

Outside the hull: an atmosphere technically breathable, technically. Dust, cold,
and silence, broken by structural groans as the Husk settles further into the crust
every decade. Nobody has mapped more than a few kilometers out. The few salvage
crews and Deep Crew scouts who go further don't always come back, and the ones who
do don't always come back making sense.

### lore_currency.md — Chits

**Chits** — physical and digital ration-tokens, originally meant to allocate food,
water, and air during the voyage. Long since become the Husk's universal currency.
Everything costs chits: air-filter cartridges, Vaultwell access, augment maintenance,
a bunk with a door that locks. Running out of chits on the Husk is not an
inconvenience. Air rationing has a schedule, and it does not care about your balance.

### Tone anchors (for gm_style.md rewrite)

- Metal, condensation, and the particular cold of recycled air.
- The ship groans. Structural settling is a constant, unremarkable background sound
  people have stopped hearing — until it isn't background.
- Light is scavenged: patched conduit, cannibalized signage, hand-strung bulbs.
  Nothing was designed to look the way it looks now.
- Class is literal altitude. Better air, better light, better food — closer to the bow.
- STEWARD's voice, when it comes, is always a small event. Nobody ignores it, even
  the people who claim not to believe in it.

---

## FACTIONS

### fac_directorate — The Directorate

Descendants of the surviving command crew. Claim legal authority over the Husk via
inherited Charter rank. Control the Bridgeworks and the upper Rings. Enforce Charter
Law through their armed arm, the **Wardens**. Gatekeep Vaultwell access permits —
the single most valuable thing they control.
**Rivals:** fac_keelrats, fac_wakeful. **Uneasy tolerance:** fac_communion (useful
for keeping the lower decks calm).
**Territory:** loc_bridgeworks, loc_rings_upper.

### fac_keelrats — The Keelrats

Scavenger syndicate that became the de facto government of everything below the
Rings. Control the Reactor Core and Cargo Fathoms, run the black market in salvaged
tech and unlicensed augments, broker illegal power taps off the reactor. Brutal
creditors, reliable partners — in Keelrat territory, their word outweighs the Charter.
**Rivals:** fac_directorate. **Transactional respect:** fac_deepcrew (they buy the
salvage Deep Crew brings back).
**Territory:** loc_enginecore, loc_cargofathoms, loc_rings_lower.

### fac_communion — The Communion of Steward

A religious order that venerates STEWARD as a wounded shepherd rather than a broken
machine — they believe the Long Fall was a sacrifice, not a failure. Maintain shrines
at old terminal rooms across the ship, especially near the Vaultwell, which they
treat as sacred ground. Radical members believe the ship's original mission can
still somehow be completed. Genuinely charitable in places — they're often the only
ones caring for the ship's forgotten and its people's forgotten alike.
**Opposed on doctrine, not usually by force:** fac_directorate (over who "really"
controls STEWARD access).
**Territory:** scattered shrines; strongest presence around loc_vaultwell.

### fac_wakeful — The Wakeful *(background faction — introduce post-MVP)*

Small, growing, and considered dangerous radicals by the Directorate. Believe the
current order is a slow-motion mass killing by inaction and push — sometimes
violently — to thaw sleepers regardless of the cost to the current population.
**Rivals:** fac_directorate, fac_keelrats (every waked sleeper is a mouth that
threatens the underdeck economy).

### fac_deepcrew — Deep Crew *(background faction — introduce post-MVP)*

Explorer's guild mapping the Deep Hull — the collapsed, unmapped aft sections of
the ship. Sell maps and salvage. Roughly neutral, hireable, thin on numbers, big
on reputation. Missing members are common and rarely discussed.

**MVP recommendation:** build fac_directorate, fac_keelrats, and fac_communion
first. Introduce fac_wakeful and fac_deepcrew in Milestone 7.

---

## LOCATIONS

Bow to stern. `danger` scored 0–5 as in HANDOFF.md.

### loc_bridgeworks — The Bridgeworks (Bow)
**danger 1.** Command Spire. Best-preserved section of the ship — real viewports
looking out over the Wastes, filtered air, working (if ancient) systems. Home to
the Charter Hall, where Directorate law is read and disputes are settled, and the
Warden barracks. **Connections:** loc_rings_upper.

### loc_rings_upper — Upper Rings
**danger 1.** The nicer half of the habitation ring corridors, closest to the
Bridgeworks. Merchant stalls with actual variety, cleaner air, Directorate patrols
visible and frequent. **Connections:** loc_bridgeworks, loc_rings_lower, loc_vaultwell.

### loc_rings_lower — Lower Rings
**danger 2.** The Scrapmarket lives here — the Husk's real economy, loud,
crowded, patched-light corridors, more Keelrat presence than Warden. Most named
NPCs who aren't faction leadership are found here. **Connections:** loc_rings_upper,
loc_enginecore, loc_cargofathoms.

### loc_vaultwell — The Vaultwell (Cryo Vaults)
**danger 2.** Cold enough to see your breath, floor to ceiling with sleeper pods,
a low hum that never stops. Heavily guarded by Wardens; a Communion shrine sits
at the main approach. Access requires a permit or a very good reason to not need one.
**Connections:** loc_rings_upper.

### loc_enginecore — The Engine Heart (Reactor Core)
**danger 3.** Unstable power, constant noise, Keelrat stronghold. Black-market
augment clinics operate in side-bays off the main reactor hall. Heat, not cold,
is the danger here. **Connections:** loc_rings_lower, loc_cargofathoms.

### loc_cargofathoms — The Cargo Fathoms
**danger 3.** The lower cargo holds, partially flooded by condensation runoff
that was never meant to pool here. Smuggling routes, deep Keelrat territory,
things stored here that were never meant to be found. **Connections:**
loc_rings_lower, loc_enginecore, loc_deephull.

### loc_deephull — The Deep Hull *(anomaly zone — introduce post-MVP)*
**danger 5.** Collapsed, unmapped aft sections. Deep Crew territory. Structural
failures, unknown hazards, salvage worth the risk if you survive it.
**Connections:** loc_cargofathoms.

### loc_wastesgate — The Wastesgate
**danger 2 (transit).** The one working airlock leading outside to the Wastes.
Guarded loosely — nobody goes out for fun, and the Directorate doesn't much care
who leaves as long as they're not bringing contraband back in. **Connections:**
loc_bridgeworks.

**MVP recommendation:** build loc_bridgeworks, loc_rings_upper, loc_rings_lower,
loc_vaultwell, loc_enginecore, loc_cargofathoms, loc_wastesgate (7 locations).
Add 3–8 smaller named sub-locations inside the Rings (a specific bar, the
Scrapmarket stalls, a Warden checkpoint) to hit the ~10-location MVP target from
HANDOFF.md. Add loc_deephull in Milestone 7.

---

## NPCS

Seed cast — enough to populate the MVP. Stats and dialogue are drafts; enrich freely.

### npc_orsa — Warden Captain Orsa
**Faction:** fac_directorate. **Location:** loc_rings_upper.
By-the-book, exhausted, not cruel — just worn down by enforcing rules she's
started to doubt. Patrols the border between the Upper and Lower Rings.
Speech: short, procedural, occasionally lets a real opinion slip when off duty.

### npc_kess — Charter Clerk Kess
**Faction:** fac_directorate. **Location:** loc_bridgeworks.
Bureaucratic gatekeeper for Vaultwell access permits. Corruptible, but expensive
and careful about it — getting caught costs him everything. Speech: precise,
transactional, never says yes or no directly.

### npc_rook — Rook
**Faction:** fac_keelrats. **Location:** loc_rings_lower (the Scrapmarket).
Fixer. Sells information and goods, brokers jobs, knows everyone worth knowing.
Genuinely likeable, which is exactly why he's dangerous. Speech: warm, quick,
always closing.

### npc_bosun_grey — Bosun Grey
**Faction:** fac_keelrats. **Location:** loc_rings_lower / loc_enginecore.
Rook's muscle. Doesn't talk much, doesn't need to. Stats should lean heavily
muscle/nerve over wits.

### npc_hale — Dr. Hale
**Faction:** fac_keelrats (loose affiliation, sells to anyone). **Location:**
loc_enginecore. Black-market augment surgeon, ex-medbay tech. Morally gray,
good at the work, doesn't ask what you're running from. Speech: clinical, dry,
occasional dark humor.

### npc_lys — Shepherd Lys
**Faction:** fac_communion. **Location:** loc_vaultwell (shrine at the approach).
Tends the shrine, quotes STEWARD's fragments like scripture, genuinely calm in
a way nobody else on the Husk manages. Speech: measured, cryptic, never raises
her voice.

### npc_ferro — Captain Ferro *(introduce with fac_deepcrew, Milestone 7)*
Deep Crew salvage captain. Gruff, pays well, missing crew members she doesn't
like to discuss. Good quest-giver for Deep Hull content.

### npc_vask — Juno Vask *(introduce with fac_wakeful, Milestone 7)*
Leader of a small Wakeful cell. Passionate, dangerous, recruiting. Believes
every year of delay is a year of murder.

### npc_teller — Teller
**Faction:** none. **Location:** loc_rings_lower.
A sleeper who was thawed early — by accident, decades before anyone planned to
wake anybody. Doesn't fully belong to the world above the ice. Sympathetic,
lost, occasionally says something that unsettles people who assume the sleepers
are just cargo. Strong hook for a personal, non-faction storyline.

### npc_steward_fragment — STEWARD (fragment/entity, not a standard NPC)
Not a person — a presence. Represent as a special entity note (`type: entity`
rather than `type: npc`) attached to specific locations (loc_vaultwell,
loc_bridgeworks, scattered terminals). Speaks rarely, unpredictably, through
speakers and screens. When it speaks, treat it as a significant scene event —
log it, don't let it happen casually. Never let STEWARD narrate mechanically
useful information the player hasn't earned through play.

---

## ITEMS

| id | name | kind | notes |
|---|---|---|---|
| itm_charter_sidearm | Charter Sidearm | weapon | Directorate-issue, well-maintained, requires a visible permit to carry openly. |
| itm_slugpipe | Slugpipe | weapon | Homemade underdeck slugthrower. Cheap, unreliable, everywhere below the Rings. |
| itm_medbay_graft | Medbay Graft | augment | Salvaged nanotech cybernetic augment. Consider adding `augment` as a formal item kind alongside weapon/consumable/key/misc. |
| itm_cryovial | Cryovial | consumable/key | Stabilized cryo-fluid. Legitimate use: safe sleeper thawing. Black-market use: illegal early-thaw procedures, usually fatal. |
| itm_access_chit | Access Chit | key | Electronic permit for restricted-deck access (Vaultwell above all). The single most fought-over item class on the Husk. |
| itm_steward_relic | Steward Relic | misc/key | Pre-Fall tech fragment carrying STEWARD's old core-language. Valuable to the Communion; good quest-item hook. |
| itm_o2_mask | Filtration Mask | misc | Required for extended time in loc_cargofathoms and loc_deephull. |

Currency (**Chits**) is not an item note — it's the abstracted resource tracked
directly on `player_state.credits` per HANDOFF.md's data model.

---

## RULES — follow-up needed

The existing `vault/rules/` files (`gm_style.md`, `narrator_rules.md`,
`parser_prompt.md`, `narration_examples.md`) were written for the old
exoplanet-colony setting. The **behavioral rules are setting-agnostic and don't
need to change** (TurnResult-is-truth, no knowledge without retrieval, etc.).
The **tone and examples do need a pass** — the "Tone anchors" section above
under LORE is the replacement material. Say the word and I'll rewrite
`gm_style.md` and `narration_examples.md` to match the Husk; `narrator_rules.md`
and `parser_prompt.md` can stay as-is.

---

## Suggested vault folder mapping for Claude Code

```
vault/
  lore/
    the_long_fall.md
    steward.md
    the_sleepers.md
    the_wastes.md
    currency.md
  factions/
    directorate.md
    keelrats.md
    communion.md
    wakeful.md        # post-MVP
    deepcrew.md        # post-MVP
  locations/
    bridgeworks.md
    rings_upper.md
    rings_lower.md
    vaultwell.md
    enginecore.md
    cargofathoms.md
    wastesgate.md
    deephull.md         # post-MVP
  npcs/
    orsa.md
    kess.md
    rook.md
    bosun_grey.md
    hale.md
    lys.md
    teller.md
    steward_fragment.md  # type: entity, not npc
    ferro.md              # post-MVP
    vask.md                # post-MVP
  items/
    charter_sidearm.md
    slugpipe.md
    medbay_graft.md
    cryovial.md
    access_chit.md
    steward_relic.md
    o2_mask.md
```

Each note's frontmatter should follow the exact schema in HANDOFF.md §4/M1
(`id`, `type`, `name`, plus the type-specific fields shown there). This
document gives Claude Code everything needed to generate all of the above as
properly frontmattered notes with body text drawn from the descriptions here.
