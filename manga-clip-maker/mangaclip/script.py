"""Data model for a clip script (what to show, say and play)."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field

SFX_NAMES = [
    "none", "whoosh", "impact", "punch", "slash", "explosion", "heartbeat",
    "sting", "chime", "boing", "rumble", "gasp",
]
MOODS = ["tense", "action", "sad", "comedic", "mysterious", "epic", "romantic", "calm"]
# How a narration line is delivered; mapped to voice rate/pitch in tts.py.
TONES = ["neutral", "tense", "excited", "whisper", "sad", "comedic"]


@dataclass
class Shot:
    box: tuple[float, float, float, float]  # normalized page coords
    narration: str = ""
    sfx: str = "none"
    emphasis: bool = False  # punch-in zoom + shake for big moments
    tone: str = "neutral"


@dataclass
class Scene:
    page: int
    shots: list[Shot] = field(default_factory=list)
    music_mood: str = ""  # empty = use the clip's mood
    music_energy: int = 3  # 1 (ambient) .. 5 (driving)


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
                                                     emphasis=sh.get("emphasis", False),
                                                     tone=sh.get("tone", "neutral"))
                                                for sh in s["shots"]],
                        music_mood=s.get("music_mood", ""), music_energy=s.get("music_energy", 3))
                  for s in d["scenes"]]
        return cls(title=d["title"], hook=d.get("hook", ""), mood=d.get("mood", "tense"),
                   outro=d.get("outro", ""), scenes=scenes)
