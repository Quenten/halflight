"""Character creator + lifepath (M7). Engine tables — deterministic given the dice.

A run starts with a class (base HP / scrip / stats / loadout) and a four-step
origin. Step 1 (upbringing) is a flat pick; steps 2-4 roll positive/neutral/
negative outcomes with authored flavor. Stats are the engine's six; item ids are
real vault items. Themed to Cinderreach.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from halflight.engine.dice import Roller

DEFAULT_START = "loc_rings_lower"


@dataclass
class Effect:
    dhp: int = 0
    dcredits: int = 0
    dstats: dict[str, int] = field(default_factory=dict)


@dataclass
class ContactSpec:
    """A person your backstory leaves you with — seeded into the run as a real NPC."""

    name: str
    relationship: str  # ally | enemy | fearful | rival | missing | contact
    note: str
    location: str = ""  # "" = whereabouts unknown / off-screen


@dataclass
class Outcome:
    kind: str  # positive | neutral | negative
    text: str
    effect: Effect = field(default_factory=Effect)
    contact: ContactSpec | None = None


@dataclass
class Option:
    id: str
    name: str
    blurb: str
    hint: str = ""
    base: Effect = field(default_factory=Effect)
    outcomes: list[Outcome] = field(default_factory=list)
    start_location: str | None = None  # where this choice leaves you (last-job step)
    contact: ContactSpec | None = None  # for flat (non-rolled) steps


@dataclass
class Step:
    id: str
    title: str
    prompt: str
    rolls: bool
    options: list[Option]


@dataclass
class ClassDef:
    id: str
    name: str
    hp: int
    credits: int
    stats: dict[str, int]
    items: list[str]
    blurb: str


CLASSES: list[ClassDef] = [
    ClassDef(
        id="enforcer", name="Enforcer", hp=24, credits=40,
        stats={"muscle": 14, "nerve": 12, "wits": 9, "tech": 8, "streetwise": 11, "presence": 10},
        items=["itm_charter_sidearm", "itm_riotshield", "itm_stimpatch"],
        blurb="You break what needs breaking. Warden or Keelrat, the work's the same and the pay's never enough.",
    ),
    ClassDef(
        id="wirehead", name="Wirehead", hp=16, credits=50,
        stats={"muscle": 8, "nerve": 10, "wits": 14, "tech": 15, "streetwise": 10, "presence": 9},
        items=["itm_toolkit", "itm_derringer"],
        blurb="The dead machines still talk, and STEWARD loudest of all. You're one of the few who bothers to listen.",
    ),
    ClassDef(
        id="fixer", name="Fixer", hp=18, credits=150,
        stats={"muscle": 9, "nerve": 12, "wits": 12, "tech": 10, "streetwise": 15, "presence": 14},
        items=["itm_lockpicks", "itm_derringer"],
        blurb="Everyone owes someone. You keep the ledger, and the ledger keeps you breathing.",
    ),
    ClassDef(
        id="chrome_rat", name="Scrapper", hp=20, credits=30,
        stats={"muscle": 11, "nerve": 13, "wits": 12, "tech": 11, "streetwise": 14, "presence": 8},
        items=["itm_keelblade", "itm_stimpatch", "itm_scrapbundle"],
        blurb="The underdecks raised you. They taught you to run, to hide, and to take.",
    ),
]


def _pos(text: str, contact: ContactSpec | None = None, **stats: int) -> Outcome:
    d = {k: v for k, v in stats.items() if k not in ("hp", "cr")}
    return Outcome("positive", text, Effect(dcredits=stats.get("cr", 0), dstats=d), contact)


def _neu(text: str, contact: ContactSpec | None = None, **stats: int) -> Outcome:
    d = {k: v for k, v in stats.items() if k not in ("hp", "cr")}
    return Outcome("neutral", text, Effect(dcredits=stats.get("cr", 0), dstats=d), contact)


def _neg(text: str, contact: ContactSpec | None = None, **stats: int) -> Outcome:
    d = {k: v for k, v in stats.items() if k not in ("hp", "cr")}
    return Outcome(
        "negative", text,
        Effect(dhp=stats.get("hp", 0), dcredits=stats.get("cr", 0), dstats=d), contact,
    )


STEPS: list[Step] = [
    Step(
        id="upbringing", title="UPBRINGING", prompt="Where did you come up?", rolls=False,
        options=[
            Option("sump", "The Cargo Fathoms", "Flooded holds, salvage, and the deep dark.",
                   "+1 streetwise", base=Effect(dstats={"streetwise": 1})),
            Option("crest", "The Bridgeworks", "Charter privilege — then the fall from it.",
                   "+1 presence", base=Effect(dstats={"presence": 1})),
            Option("crew", "A Keelrat crew", "Loyalty was survival.",
                   "+1 muscle", base=Effect(dstats={"muscle": 1})),
            Option("offworld", "Thawed from the ice", "You woke from the Vaultwell with the world already old.",
                   "+1 nerve", base=Effect(dstats={"nerve": 1})),
        ],
    ),
    Step(
        id="marked", title="WHAT MARKED YOU", prompt="What changed everything?", rolls=True,
        options=[
            Option("betrayal", "Betrayal", "Someone you trusted.", "±presence", outcomes=[
                _pos("They tried to bury you and missed. You came out sharper, and you kept the leverage.",
                     ContactSpec("Wick", "fearful", "Tried to sell you out. You turned it around and kept the "
                                 "recordings — now they flinch when you call."), presence=1, cr=30),
                _neu("It cost you a friend and taught you a lesson. Even trade.", presence=0),
                _neg("It broke something you haven't gotten back. You trust no one now.",
                     ContactSpec("Wick", "enemy", "Sold you out and walked away clean. You haven't settled it."),
                     presence=-1, cr=-20),
            ]),
            Option("violence", "Violence", "You survived what shouldn't be survivable.", "±nerve ±muscle", outcomes=[
                _pos("You walked away from it harder than you went in. Scars, but the good kind.", nerve=1, muscle=1),
                _neu("You lived. Barely. You don't talk about it.", nerve=1),
                _neg("Something in you didn't heal right. The shakes come at bad times.", nerve=-1, hp=-4),
            ]),
            Option("ambition", "Ambition", "You reached too high.", "±presence", outcomes=[
                _pos("The scheme paid. You made chits and made enemies, and the chits were worth it.", presence=1, cr=60),
                _neu("A complicated outcome. Made some chits, made some enemies. Broke even.", cr=20),
                _neg("It collapsed and took your name with it. You're starting over.", presence=-1, cr=-30),
            ]),
            Option("discovery", "Discovery", "You learned something dangerous.", "±wits ±tech", outcomes=[
                _pos("You understood it before it understood you. That knowledge still pays.", wits=1, tech=1, cr=20),
                _neu("You know a thing you can't unknow. It hasn't cost you yet.", wits=1),
                _neg("Someone found out you know. Now you look over your shoulder.", tech=-1, cr=-10),
            ]),
        ],
    ),
    Step(
        id="ran_with", title="WHO YOU RAN WITH", prompt="Who pulled you into their orbit?", rolls=True,
        options=[
            Option("fixer", "A Scrapmarket fixer", "Work for hire, no questions.", "±streetwise", outcomes=[
                _pos("The work was steady and the fixer square with you. You banked a stake.",
                     ContactSpec("Corva", "ally", "A Scrapmarket fixer who dealt square with you. Owes you "
                                 "nothing, but she takes your calls."), streetwise=1, cr=50),
                _neu("Jobs came and went. You're neither ahead nor behind.", streetwise=0),
                _neg("The fixer set you up as the fall. You did time; they vanished.",
                     ContactSpec("Corva", "enemy", "Set you up as the fall and vanished while you did the time."),
                     streetwise=-1, cr=-40),
            ]),
            Option("gutter", "A gutter crew", "Family, until it wasn't.", "±muscle", outcomes=[
                _pos("They had your back and you had theirs. You came out tougher and connected.",
                     ContactSpec("Marn", "ally", "Ran the gutter crew you came up in. Still owes you a couple of "
                                 "favors and a share."), muscle=1, cr=20),
                _neu("You ran with them a while. It ended quietly.", muscle=1),
                _neg("It ended in blood, and not theirs alone. You still owe for it.",
                     ContactSpec("Marn", "rival", "Your old crew boss. It ended in blood and you still owe for "
                                 "it."), muscle=-1, hp=-4),
            ]),
            Option("handler", "A Directorate handler", "Clean work, dirty hands.", "±tech", outcomes=[
                _pos("The Directorate paid well and taught you their systems. You kept the access.", tech=1, cr=60),
                _neu("Clean jobs, clean pay, no loyalty either way.", tech=1),
                _neg("They used you up and cut you loose with a debt you can't clear.",
                     ContactSpec("Dossen", "enemy", "The Directorate handler who used you up and cut you loose "
                                 "with a debt you can't clear."), tech=-1, cr=-30),
            ]),
            Option("alone", "Nobody", "You worked alone. Still do.", "±streetwise ±nerve", outcomes=[
                _pos("No one to sell you out, no cut to pay. You kept everything you earned.", streetwise=1, nerve=1, cr=40),
                _neu("Alone is quieter. Alone is slower. You made it work.", nerve=1),
                _neg("Alone means no one comes when it goes wrong. It went wrong.", nerve=-1, hp=-4),
            ]),
        ],
    ),
    Step(
        id="last_job", title="THE LAST JOB", prompt="What was the last job before you ended up here?", rolls=True,
        options=[
            Option("salvage", "A salvage run toward the Deep Hull", "The score to set you up.", "±wits",
                   start_location="loc_cargofathoms", outcomes=[
                _pos("You came back with something the Deep Crew would kill for, and the chits to match.", wits=1, cr=80),
                _neu("You came back. Half the crew didn't. The haul barely covered the loss.", wits=1),
                _neg("The Deep Hull took the haul and two fingers. You limped back with nothing.", wits=-1, hp=-6, cr=-20),
            ]),
            Option("protection", "A protection job", "Someone needed you. You showed up.", "±nerve ±muscle",
                   start_location="loc_rings_lower", outcomes=[
                _pos("You kept them alive and they paid what they promised. Rare, that.",
                     ContactSpec("Dr. Sabec", "ally", "You kept them alive. They run a clinic here and the debt "
                                 "runs your way now.", location="loc_rings_lower"), nerve=1, muscle=1, cr=40),
                _neu("You held the line. It cost more than it paid, but you held it.", nerve=1),
                _neg("They died on your watch. You carry that, and the debt that came with it.",
                     ContactSpec("Dr. Sabec", "missing", "Died on your watch — or was taken. You never found the "
                                 "body, and you still carry it."), muscle=-1, hp=-6),
            ]),
            Option("double_cross", "A double-cross", "You sold out the people who trusted you.", "±presence",
                   start_location="loc_scrapmarket", outcomes=[
                _pos("The betrayal paid clean and no one traced it back. Your conscience is negotiable.", presence=1, cr=70),
                _neu("You got out with the chits and a name people spit. Worth it, mostly.", cr=30, presence=-1),
                _neg("They found out. You barely made the lower decks ahead of them.",
                     ContactSpec("Rhet", "enemy", "You sold out their crew. They found out, and they're still "
                                 "looking."), presence=-1, hp=-4, cr=-10),
            ]),
            Option("runner", "A runner", "You ran from everything you'd built.", "±nerve",
                   start_location="loc_rings_lower", outcomes=[
                _pos("You got out clean and early, and took a stake with you. Smart.", nerve=1, cr=40),
                _neu("You ran. You're here. That's all that matters now.", nerve=1),
                _neg("You ran with nothing but the debt, and it followed you down.", nerve=-1, cr=-30),
            ]),
        ],
    ),
]


@dataclass
class BuildStep:
    step_id: str
    step_title: str
    option_name: str
    outcome_kind: str
    text: str
    summary: str
    contact: ContactSpec | None = None


@dataclass
class Build:
    hp: int
    credits: int
    stats: dict[str, int]
    inventory: dict[str, int]
    start_location: str
    backstory: list[BuildStep]
    contacts: list[ContactSpec] = field(default_factory=list)


def get_class(class_id: str) -> ClassDef | None:
    return next((c for c in CLASSES if c.id == class_id), None)


def _roll(outcomes: list[Outcome], dice: Roller) -> Outcome:
    by_kind = {o.kind: o for o in outcomes}
    r = dice.d20()
    if r >= 14 and "positive" in by_kind:
        return by_kind["positive"]
    if r <= 7 and "negative" in by_kind:
        return by_kind["negative"]
    return by_kind.get("neutral", outcomes[0])


def _apply(eff: Effect, hp: int, credits: int, stats: dict[str, int]) -> tuple[int, int]:
    for k, v in eff.dstats.items():
        stats[k] = stats.get(k, 10) + v
    return hp + eff.dhp, credits + eff.dcredits


def summarize_effect(eff: Effect) -> str:
    parts: list[str] = []
    if eff.dhp:
        parts.append(f"{eff.dhp:+d} HP")
    if eff.dcredits:
        parts.append(f"{eff.dcredits:+d} scrip")
    parts += [f"{v:+d} {k}" for k, v in eff.dstats.items()]
    return " · ".join(parts) or "no change"


_summary = summarize_effect  # internal alias


def get_step(step_id: str) -> Step | None:
    return next((s for s in STEPS if s.id == step_id), None)


def _outcome_for_kind(opt: Option, kind: str) -> Outcome:
    by_kind = {o.kind: o for o in opt.outcomes}
    return by_kind.get(kind) or by_kind.get("neutral") or opt.outcomes[0]


def preview_step(step_id: str, option_id: str, dice: Roller) -> Outcome | None:
    """Roll (or resolve) one lifepath step in isolation, so the creator can show its
    result the moment the player picks it. Flat steps return a 'chosen' outcome."""
    step = get_step(step_id)
    if step is None:
        return None
    opt = next((o for o in step.options if o.id == option_id), None)
    if opt is None:
        return None
    if step.rolls and opt.outcomes:
        return _roll(opt.outcomes, dice)
    return Outcome("chosen", opt.blurb, opt.base, opt.contact)


def resolve_build(
    class_id: str,
    choices: dict[str, str],
    dice: Roller,
    outcomes: dict[str, str] | None = None,
) -> Build:
    cls = get_class(class_id)
    if cls is None:
        raise ValueError(f"unknown class {class_id}")
    hp, credits = cls.hp, cls.credits
    stats = dict(cls.stats)
    inventory = {item: 1 for item in cls.items}
    start_location = DEFAULT_START
    backstory: list[BuildStep] = []
    contacts: list[ContactSpec] = []

    for step in STEPS:
        opt = next((o for o in step.options if o.id == choices.get(step.id)), None)
        if opt is None:
            continue
        if opt.start_location:
            start_location = opt.start_location
        if step.rolls and opt.outcomes:
            forced = (outcomes or {}).get(step.id)
            if forced in ("positive", "neutral", "negative"):
                outcome = _outcome_for_kind(opt, forced)
            else:
                outcome = _roll(opt.outcomes, dice)
            hp, credits = _apply(outcome.effect, hp, credits, stats)
            contact = outcome.contact
            backstory.append(
                BuildStep(step.id, step.title, opt.name, outcome.kind, outcome.text,
                          _summary(outcome.effect), contact)
            )
        else:
            hp, credits = _apply(opt.base, hp, credits, stats)
            contact = opt.contact
            backstory.append(
                BuildStep(step.id, step.title, opt.name, "chosen", opt.blurb,
                          _summary(opt.base), contact)
            )
        if contact is not None:
            contacts.append(contact)

    return Build(
        hp=max(1, hp), credits=max(0, credits), stats=stats, inventory=inventory,
        start_location=start_location, backstory=backstory, contacts=contacts,
    )
