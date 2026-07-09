---
id: loc_<slug>              # permanent, unique, snake_case, loc_ prefix
type: location
name: <display name>
district: <district_slug>
danger: 0                   # 0-5
connections: [loc_x, loc_y] # location ids reachable from here
tags: [public, transit]
---

<Narrator flavor and lore. Free markdown. Second person is fine in the body but
this text is context for the narrator, not shown verbatim.>

Wikilinks like [[npc_x]] or [[fac_y]] define graph relationships beyond the
frontmatter. Every [[id]] must resolve to a real note.

## Secret

<Hidden until an engine event flips this section's `revealed` flag. Excluded from
retrieval until then. Anything the player shouldn't know yet goes here.>
