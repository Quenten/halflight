"""Character creator + lifepath (M7). Engine tables — deterministic given the dice.

A run starts with a class (base HP / scrip / stats / loadout) and a four-step
origin. Step 1 (upbringing) is a flat pick; steps 2-4 roll positive/neutral/
negative outcomes with authored flavor. Stats are the engine's six; item ids are
real vault items. Themed to Cinderreach.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from halflight.engine.dice import Roller

DEFAULT_START = "loc_saltgate"


@dataclass
class Effect:
    dhp: int = 0
    dcredits: int = 0
    dstats: dict[str, int] = field(default_factory=dict)


@dataclass
class Outcome:
    kind: str  # positive | neutral | negative
    text: str
    effect: Effect = field(default_factory=Effect)


@dataclass
class Option:
    id: str
    name: str
    blurb: str
    hint: str = ""
    base: Effect = field(default_factory=Effect)
    outcomes: list[Outcome] = field(default_factory=list)
    start_location: str | None = None  # where this choice leaves you (last-job step)


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
        items=["itm_rail_maul", "itm_stimshot"],
        blurb="You break what needs breaking. The Saltline pays for that, when it pays.",
    ),
    ClassDef(
        id="wirehead", name="Wirehead", hp=16, credits=50,
        stats={"muscle": 8, "nerve": 10, "wits": 14, "tech": 15, "streetwise": 10, "presence": 9},
        items=["itm_slug_pistol", "itm_relay_key"],
        blurb="The dead machines still talk. You're one of the few who bothers to listen.",
    ),
    ClassDef(
        id="fixer", name="Fixer", hp=18, credits=150,
        stats={"muscle": 9, "nerve": 12, "wits": 12, "tech": 10, "streetwise": 15, "presence": 14},
        items=["itm_ledger_chit", "itm_slug_pistol"],
        blurb="Everyone owes someone. You keep the ledger, and the ledger keeps you.",
    ),
    ClassDef(
        id="chrome_rat", name="Chrome Rat", hp=20, credits=30,
        stats={"muscle": 11, "nerve": 13, "wits": 12, "tech": 11, "streetwise": 14, "presence": 8},
        items=["itm_shiv", "itm_stimshot", "itm_scrap_bundle"],
        blurb="The Undervault raised you. It taught you to run, to hide, and to take.",
    ),
]


def _pos(text: str, **stats: int) -> Outcome:
    d = {k: v for k, v in stats.items() if k not in ("hp", "cr")}
    return Outcome("positive", text, Effect(dcredits=stats.get("cr", 0), dstats=d))


def _neu(text: str, **stats: int) -> Outcome:
    d = {k: v for k, v in stats.items() if k not in ("hp", "cr")}
    return Outcome("neutral", text, Effect(dcredits=stats.get("cr", 0), dstats=d))


def _neg(text: str, **stats: int) -> Outcome:
    d = {k: v for k, v in stats.items() if k not in ("hp", "cr")}
    return Outcome("negative", text, Effect(dhp=stats.get("hp", 0), dcredits=stats.get("cr", 0), dstats=d))


STEPS: list[Step] = [
    Step(
        id="upbringing", title="UPBRINGING", prompt="Where did you come up?", rolls=False,
        options=[
            Option("sump", "The sump tunnels", "Survival instinct. Hidden routes.",
                   "+1 streetwise", base=Effect(dstats={"streetwise": 1})),
            Option("crest", "A Crest arcology", "Privilege, then the fall.",
                   "+1 presence", base=Effect(dstats={"presence": 1})),
            Option("crew", "A syndicate crew", "Loyalty was survival.",
                   "+1 muscle", base=Effect(dstats={"muscle": 1})),
            Option("offworld", "Offworld, inbound", "You came here chasing something.",
                   "+1 nerve", base=Effect(dstats={"nerve": 1})),
        ],
    ),
    Step(
        id="marked", title="WHAT MARKED YOU", prompt="What changed everything?", rolls=True,
        options=[
            Option("betrayal", "Betrayal", "Someone you trusted.", "±presence", outcomes=[
                _pos("They tried to bury you and missed. You came out sharper, and you kept the leverage.", presence=1, cr=30),
                _neu("It cost you a friend and taught you a lesson. Even trade.", presence=0),
                _neg("It broke something you haven't gotten back. You trust no one now.", presence=-1, cr=-20),
            ]),
            Option("violence", "Violence", "You survived what shouldn't be survivable.", "±nerve ±muscle", outcomes=[
                _pos("You walked away from it harder than you went in. Scars, but the good kind.", nerve=1, muscle=1),
                _neu("You lived. Barely. You don't talk about it.", nerve=1),
                _neg("Something in you didn't heal right. The shakes come at bad times.", nerve=-1, hp=-4),
            ]),
            Option("ambition", "Ambition", "You reached too high.", "±presence", outcomes=[
                _pos("The scheme paid. You made money and made enemies, and the money was worth it.", presence=1, cr=60),
                _neu("A complicated outcome. Made some money, made some enemies. Broke even.", cr=20),
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
            Option("fixer", "A Saltline fixer", "Work for hire, no questions.", "±streetwise", outcomes=[
                _pos("The work was steady and the fixer square with you. You banked a stake.", streetwise=1, cr=50),
                _neu("Jobs came and went. You're neither ahead nor behind.", streetwise=0),
                _neg("The fixer set you up as the fall. You did time; they vanished.", streetwise=-1, cr=-40),
            ]),
            Option("gutter", "A gutter crew", "Family, until it wasn't.", "±muscle", outcomes=[
                _pos("They had your back and you had theirs. You came out tougher and connected.", muscle=1, cr=20),
                _neu("You ran with them a while. It ended quietly.", muscle=1),
                _neg("It ended in blood, and not theirs alone. You still owe for it.", muscle=-1, hp=-4),
            ]),
            Option("handler", "A Combine handler", "Clean work, dirty hands.", "±tech", outcomes=[
                _pos("The Combine paid well and taught you their tools. You kept the tools.", tech=1, cr=60),
                _neu("Clean jobs, clean pay, no loyalty either way.", tech=1),
                _neg("They used you up and cut you loose with a ledger-tag you can't clear.", tech=-1, cr=-30),
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
            Option("salvage", "A salvage run past the Seam", "The score to set you up.", "±wits",
                   start_location="loc_walker_bay", outcomes=[
                _pos("You came back with something the Dredge would kill for, and the scrip to match.", wits=1, cr=80),
                _neu("You came back. Half the crew didn't. The haul barely covered the loss.", wits=1),
                _neg("The Reach took the haul and two fingers. You limped back with nothing.", wits=-1, hp=-6, cr=-20),
            ]),
            Option("protection", "A protection job", "Someone needed you. You showed up.", "±nerve ±muscle",
                   start_location="loc_ashwell", outcomes=[
                _pos("You kept them alive and they paid what they promised. Rare, that.", nerve=1, muscle=1, cr=40),
                _neu("You held the line. It cost more than it paid, but you held it.", nerve=1),
                _neg("They died on your watch. You carry that, and the debt that came with it.", muscle=-1, hp=-6),
            ]),
            Option("double_cross", "A double-cross", "You sold out the people who trusted you.", "±presence",
                   start_location="loc_drip_market", outcomes=[
                _pos("The betrayal paid clean and no one traced it back. Your conscience is negotiable.", presence=1, cr=70),
                _neu("You got out with the scrip and a name people spit. Worth it, mostly.", cr=30, presence=-1),
                _neg("They found out. You barely made the Undervault ahead of them.", presence=-1, hp=-4, cr=-10),
            ]),
            Option("runner", "A runner", "You ran from everything you'd built.", "±nerve",
                   start_location="loc_saltgate", outcomes=[
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


@dataclass
class Build:
    hp: int
    credits: int
    stats: dict[str, int]
    inventory: dict[str, int]
    start_location: str
    backstory: list[BuildStep]


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


def _summary(eff: Effect) -> str:
    parts: list[str] = []
    if eff.dhp:
        parts.append(f"{eff.dhp:+d} HP")
    if eff.dcredits:
        parts.append(f"{eff.dcredits:+d} scrip")
    parts += [f"{v:+d} {k}" for k, v in eff.dstats.items()]
    return " · ".join(parts) or "no change"


def resolve_build(class_id: str, choices: dict[str, str], dice: Roller) -> Build:
    cls = get_class(class_id)
    if cls is None:
        raise ValueError(f"unknown class {class_id}")
    hp, credits = cls.hp, cls.credits
    stats = dict(cls.stats)
    inventory = {item: 1 for item in cls.items}
    start_location = DEFAULT_START
    backstory: list[BuildStep] = []

    for step in STEPS:
        opt = next((o for o in step.options if o.id == choices.get(step.id)), None)
        if opt is None:
            continue
        if opt.start_location:
            start_location = opt.start_location
        if step.rolls and opt.outcomes:
            outcome = _roll(opt.outcomes, dice)
            hp, credits = _apply(outcome.effect, hp, credits, stats)
            backstory.append(
                BuildStep(step.id, step.title, opt.name, outcome.kind, outcome.text,
                          _summary(outcome.effect))
            )
        else:
            hp, credits = _apply(opt.base, hp, credits, stats)
            backstory.append(
                BuildStep(step.id, step.title, opt.name, "chosen", opt.blurb, _summary(opt.base))
            )

    return Build(
        hp=max(1, hp), credits=max(0, credits), stats=stats, inventory=inventory,
        start_location=start_location, backstory=backstory,
    )
