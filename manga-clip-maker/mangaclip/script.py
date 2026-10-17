"""Data model for a clip script (what to show, say and play)."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field

SFX_NAMES = [
    "none", "whoosh", "impact", "punch", "slash", "explosion", "heartbeat",
    "sting", "chime", "boing", "rumble", "gasp",
]
MOODS = ["tense", "action", "sad", "comedic", "mysterious", "epic", "romantic", "calm"]


@dataclass
class Shot:
    box: tuple[float, float, float, float]  # normalized page coords
    narration: str = ""
    sfx: str = "none"
    emphasis: bool = False  # punch-in zoom + shake for big moments


@dataclass
class Scene:
    page: int
    shots: list[Shot] = field(default_factory=list)


@dataclass
class ClipScript:
    title: str
    hook: str
    mood: str
    outro: str
    scenes: list[Scene]

    @property
    def pages(self) -> list[int]:
        return [s.page for s in self.scenes]

    def to_json(self) -> str:
        return json.dumps(asdict(self), indent=2, ensure_ascii=False)

    @classmethod
    def from_dict(cls, d: dict) -> "ClipScript":
        scenes = [Scene(page=s["page"], shots=[Shot(box=tuple(sh["box"]),
                                                     narration=sh.get("narration", ""),
                                                     sfx=sh.get("sfx", "none"),
                                                     emphasis=sh.get("emphasis", False))
                                                for sh in s["shots"]])
                  for s in d["scenes"]]
        return cls(title=d["title"], hook=d.get("hook", ""), mood=d.get("mood", "tense"),
                   outro=d.get("outro", ""), scenes=scenes)
