---
id: npc_<slug>
type: npc
name: <display name>
faction: fac_<slug>         # or null
role: <freeform>
location: loc_<slug>        # home/default
disposition_default: 0      # -100..100
stats: {muscle: 10, nerve: 10, wits: 10, tech: 10, streetwise: 10, presence: 10}
hp: 15
schedule: {day: loc_x, night: loc_y}   # optional; values are location ids
alive: true
---

<Who they are, how they talk, what they want. Narrator flavor.>

Relationships via wikilinks: works for [[fac_x]], rivals with [[npc_y]].

## Secret

<What this NPC hides. Revealed only through play.>
