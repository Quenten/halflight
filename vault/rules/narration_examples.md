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
> You swung the wrench and caught Dovan under the ribs. He doubled over against the
> railing, winded, and grabbed for the knife on his belt. The machines on the floor
> kept running, and nobody looked over.
>
> Dovan got the knife free. He wasn't going to let this go.

## Example 2 — failed check

TurnResult:
```json
{"action":{"kind":"custom","description":"pick the lock on the depot door","stat_hint":"tech"},
 "valid":true,"roll":6,"difficulty":15,"outcome":"failure",
 "state_changes":[],"scene_events":[{"kind":"noise_made","detail":{"level":"low"}}]}
```

Narration:
> The lock was old and stubborn. Your pick slipped off the same pin twice, and on the
> third try the tip snapped off inside it. The door stayed shut.
>
> Somewhere down the alley you heard a scuff — a footstep, or just the wind moving a
> loose panel. You couldn't tell which.

## Example 3 — lore question with no retrieval hit

Player asked NPC about "the Provost's daughter". No chunk retrieved.

TurnResult:
```json
{"action":{"kind":"talk","target":"npc_vesna","topic":"the Provost's daughter"},
 "valid":true,"roll":null,"difficulty":null,"outcome":"narrative_only",
 "state_changes":[],"scene_events":[]}
```

Narration:
> Vesna repeated the name back, like she wasn't sure it was real. "Provost's daughter."
> She shook her head. "You've got the wrong person, or the wrong name." Then she went
> back to her manifest. She wasn't going to give you anything for free.
