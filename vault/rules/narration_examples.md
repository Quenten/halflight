# Narration Examples (few-shot)

Two or three of these are appended to the narrator prompt as examples.
Replace with better ones as real play produces them — logged turns are the source.

---

## Example 1 — successful attack

TurnResult:
```json
{"action":{"kind":"attack","target":"npc_dovan","method":"pipe wrench"},
 "valid":true,"roll":17,"difficulty":13,"outcome":"success",
 "state_changes":[{"entity":"npc_dovan","field":"hp","delta":-6}],
 "scene_events":[{"kind":"attack_hit","detail":{"damage":6}},
                 {"kind":"npc_hostile","detail":{"npc":"npc_dovan"}}]}
```

Narration:
> You swung the wrench low and caught Dovan under the ribs. He folded against the
> railing, breath gone, one hand scrabbling for the knife on his belt. Behind you the
> reclaimer line kept hammering — nobody on the floor so much as turned.
>
> Dovan got the knife loose. He wasn't leaving now.

## Example 2 — failed check

TurnResult:
```json
{"action":{"kind":"custom","description":"pick the lock on the depot door","stat_hint":"tech"},
 "valid":true,"roll":6,"difficulty":15,"outcome":"failure",
 "state_changes":[],"scene_events":[{"kind":"noise_made","detail":{"level":"low"}}]}
```

Narration:
> The lock was older than you and meaner. Your pick skated off the third pin twice,
> then snapped a half-centimeter of tip into the housing. The door didn't care.
>
> Down the alley, something shifted — a boot on grating, maybe, or just the wind
> working a loose panel. Hard to say.

## Example 3 — lore question with no retrieval hit

Player asked NPC about "the Provost's daughter". No chunk retrieved.

TurnResult:
```json
{"action":{"kind":"talk","target":"npc_vesna","topic":"the Provost's daughter"},
 "valid":true,"roll":null,"difficulty":null,"outcome":"narrative_only",
 "state_changes":[],"scene_events":[]}
```

Narration:
> Vesna turned the name over like a coin she suspected was fake. "Provost's daughter."
> She shook her head once. "You're asking the wrong person. Or it's the wrong name."
> She went back to her manifest. The conversation had a price, and you hadn't paid it.
