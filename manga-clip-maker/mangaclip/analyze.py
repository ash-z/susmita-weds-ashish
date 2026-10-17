"""Find the interesting parts of a manga and write narration scripts.

Two engines:
  * ClaudeAnalyzer  - reads the pages with Claude vision, scores every page,
                      then writes a panel-by-panel narration script.
  * HeuristicAnalyzer - offline fallback: scores pages on visual intensity and
                      uses detected panels with minimal narration.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass

from .panels import detect_panels, snap, sort_reading_order, visual_stats
from .pdf import Page
from .script import MOODS, SFX_NAMES, ClipScript, Scene, Shot

log = logging.getLogger(__name__)

MODEL = "claude-opus-5-5"


@dataclass
class PageInfo:
    page: int
    summary: str
    score: float  # 0-10, how clip-worthy the page is
    is_story: bool = True


def pick_segments(infos: list[PageInfo], pages_per_clip: int, num_clips: int) -> list[list[int]]:
    """Pick non-overlapping windows of consecutive story pages with the best scores."""
    candidates = []
    for i in range(len(infos) - pages_per_clip + 1):
        window = infos[i:i + pages_per_clip]
        if not all(w.is_story for w in window):
            continue
        # Weight the last page a bit more: clips that end on a peak feel better.
        score = sum(w.score for w in window) + 0.5 * window[-1].score
        candidates.append((score, [w.page for w in window]))
    if not candidates:  # e.g. fewer story pages than pages_per_clip
        story = [i.page for i in infos if i.is_story] or [i.page for i in infos]
        return [story[:pages_per_clip]]
    chosen: list[list[int]] = []
    used: set[int] = set()
    for _, pages in sorted(candidates, key=lambda c: -c[0]):
        if used.isdisjoint(pages):
            chosen.append(pages)
            used.update(pages)
        if len(chosen) == num_clips:
            break
    return sorted(chosen)


# --------------------------------------------------------------------------- Claude

SCAN_SCHEMA = {
    "type": "object",
    "properties": {
        "pages": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "page": {"type": "integer"},
                    "summary": {"type": "string"},
                    "score": {"type": "integer"},
                    "is_story": {"type": "boolean"},
                },
                "required": ["page", "summary", "score", "is_story"],
                "additionalProperties": False,
            },
        },
    },
    "required": ["pages"],
    "additionalProperties": False,
}

SCRIPT_SCHEMA = {
    "type": "object",
    "properties": {
        "title": {"type": "string"},
        "hook": {"type": "string"},
        "mood": {"type": "string", "enum": MOODS},
        "outro": {"type": "string"},
        "scenes": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "page": {"type": "integer"},
                    "shots": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "box": {"type": "array", "items": {"type": "integer"}},
                                "narration": {"type": "string"},
                                "sfx": {"type": "string", "enum": SFX_NAMES},
                                "emphasis": {"type": "boolean"},
                            },
                            "required": ["box", "narration", "sfx", "emphasis"],
                            "additionalProperties": False,
                        },
                    },
                },
                "required": ["page", "shots"],
                "additionalProperties": False,
            },
        },
    },
    "required": ["title", "hook", "mood", "outro", "scenes"],
    "additionalProperties": False,
}

SYSTEM = """You are the writer and editor of a manga recap channel that makes short, \
punchy vertical video clips. You read manga pages carefully (including speech bubbles \
and sound-effect lettering) and explain what is happening in an engaging, spoiler-aware \
voice-over, the way a good storyteller recaps a scene for someone watching along."""


class ClaudeAnalyzer:
    def __init__(self, language: str = "English", right_to_left: bool = True,
                 scan_batch: int = 16, effort: str = "medium"):
        import anthropic

        self.client = anthropic.Anthropic()
        self.language = language
        self.rtl = right_to_left
        self.scan_batch = scan_batch
        self.effort = effort

    def _ask(self, content: list, schema: dict, max_tokens: int = 16000) -> dict:
        with self.client.beta.messages.stream(
            model=MODEL,
            max_tokens=max_tokens,
            system=SYSTEM,
            betas=["server-side-fallback-2026-07-01"],
            fallbacks="default",
            output_config={"effort": self.effort,
                           "format": {"type": "json_schema", "schema": schema}},
            messages=[{"role": "user", "content": content}],
        ) as stream:
            msg = stream.get_final_message()
        if msg.stop_reason == "refusal":
            raise RuntimeError(f"Claude declined this request: {msg.stop_details}")
        if msg.stop_reason == "max_tokens":
            raise RuntimeError("Claude's response was cut off (max_tokens); try fewer pages per request")
        text = "".join(b.text for b in msg.content if b.type == "text")
        return json.loads(text)

    def scan(self, pages: list[Page]) -> list[PageInfo]:
        """Score every page, in batches, carrying the story so far forward."""
        infos: list[PageInfo] = []
        for i in range(0, len(pages), self.scan_batch):
            batch = pages[i:i + self.scan_batch]
            log.info("Scanning pages %d-%d", batch[0].number, batch[-1].number)
            story_so_far = "\n".join(f"p{x.page}: {x.summary}" for x in infos[-40:])
            content: list = []
            for p in batch:
                content.append({"type": "text", "text": f"Page {p.number}:"})
                content.append({"type": "image", "source": {
                    "type": "base64", "media_type": "image/jpeg", "data": p.jpeg_b64(1024)}})
            content.append({"type": "text", "text": f"""\
Story so far (from earlier pages):
{story_so_far or "(this is the start of the file)"}

For each page above, give:
- summary: one sentence on what happens (who, what), in English.
- score: 0-10, how good this page is as part of a short narrated clip. High scores go to \
reveals, fights, big emotional beats, twists, cliffhangers, funny gags and striking splash \
art. Low scores go to quiet transitions and exposition.
- is_story: false for covers, credits, table of contents, ads, afterwords or blank pages."""})
            data = self._ask(content, SCAN_SCHEMA)
            by_page = {d["page"]: d for d in data["pages"]}
            for p in batch:
                d = by_page.get(p.number, {"summary": "", "score": 0, "is_story": True})
                infos.append(PageInfo(p.number, d["summary"],
                                      float(max(0, min(10, d["score"]))), d["is_story"]))
        return infos

    def write_script(self, pages: list[Page], infos: list[PageInfo],
                     target_seconds: int) -> ClipScript:
        first = pages[0].number
        context = "\n".join(f"p{x.page}: {x.summary}" for x in infos if x.page < first)
        direction = "right-to-left (Japanese manga)" if self.rtl else "left-to-right"
        content: list = []
        for p in pages:
            content.append({"type": "text", "text": f"Page {p.number}:"})
            content.append({"type": "image", "source": {
                "type": "base64", "media_type": "image/jpeg", "data": p.jpeg_b64(1568)}})
        content.append({"type": "text", "text": f"""\
Story context before these pages:
{context or "(these are the first pages)"}

Write a narrated clip of about {target_seconds} seconds covering the pages above.

- title: a short catchy title for the clip.
- hook: one opening line (under 15 words) that makes viewers stay.
- mood: overall mood, used to choose background music.
- scenes: one per page, in order. Each has the panels to show as `shots`, in {direction} \
reading order. Use the panels that carry the story; skip filler panels.
  - box: [x0, y0, x1, y1] bounding box of the panel on a 0-1000 scale of the page \
width/height (origin top-left). Fit the panel border tightly.
  - narration: what the narrator says while this panel is on screen, 0-25 words. \
Present tense, vivid, explain the dialogue instead of reading every bubble. Leave it \
empty for a panel that should just breathe (a big impact, a silent stare).
  - sfx: a sound effect that fits the panel (match drawn sound-effect lettering when \
there is any), or "none". Use sfx sparingly, not on every panel.
  - emphasis: true only for the one or two biggest moments (adds a punch-in zoom).
- outro: a closing line, e.g. a cliffhanger question.

Write all narration, hook, title and outro in {self.language}."""})
        data = self._ask(content, SCRIPT_SCHEMA)
        return self._to_script(data, pages)

    def _to_script(self, data: dict, pages: list[Page]) -> ClipScript:
        by_num = {p.number: p for p in pages}
        scenes = []
        for s in data["scenes"]:
            page = by_num.get(s["page"])
            if page is None:
                continue
            detected = detect_panels(page.image, self.rtl)
            shots = []
            for sh in s["shots"]:
                b = [max(0, min(1000, v)) / 1000 for v in (sh["box"] + [0, 0, 1000, 1000])[:4]]
                box = (min(b[0], b[2]), min(b[1], b[3]), max(b[0], b[2]), max(b[1], b[3]))
                if box[2] - box[0] < 0.05 or box[3] - box[1] < 0.05:
                    box = (0.0, 0.0, 1.0, 1.0)
                shots.append(Shot(box=snap(box, detected), narration=sh["narration"].strip(),
                                  sfx=sh["sfx"], emphasis=sh["emphasis"]))
            if shots:
                scenes.append(Scene(page=page.number, shots=shots))
        if not scenes:
            raise RuntimeError("Claude returned a script with no usable scenes")
        return ClipScript(title=data["title"], hook=data["hook"], mood=data["mood"],
                          outro=data["outro"], scenes=scenes)


# --------------------------------------------------------------------------- offline

class HeuristicAnalyzer:
    """No-API fallback: picks visually intense pages and pans across detected panels."""

    def __init__(self, right_to_left: bool = True, title: str = "Manga highlight"):
        self.rtl = right_to_left
        self.title = title

    def scan(self, pages: list[Page]) -> list[PageInfo]:
        stats = [visual_stats(p.image) for p in pages]
        edges = [s["edges"] for s in stats]
        lo, hi = min(edges), max(edges)
        infos = []
        for p, s in zip(pages, stats):
            n_panels = len(detect_panels(p.image, self.rtl))
            busy = (s["edges"] - lo) / (hi - lo + 1e-9)  # speed lines, effects, action
            splash = 1.0 if n_panels <= 2 else 0.0  # big panels = big moments
            blank = s["ink"] < 0.03
            score = 0 if blank else 10 * (0.65 * busy + 0.35 * splash)
            infos.append(PageInfo(p.number, "", score, is_story=not blank))
        # The first page of a PDF is usually the cover.
        if len(infos) > 3:
            infos[0].is_story = False
        return infos

    def write_script(self, pages: list[Page], infos: list[PageInfo],
                     target_seconds: int) -> ClipScript:
        scenes = []
        for p in pages:
            boxes = sort_reading_order(detect_panels(p.image, self.rtl), self.rtl)[:6]
            shots = [Shot(box=b) for b in boxes]
            big = max(range(len(shots)),
                      key=lambda i: (boxes[i][2] - boxes[i][0]) * (boxes[i][3] - boxes[i][1]))
            shots[big].sfx, shots[big].emphasis = "impact", True
            if shots[0].sfx == "none":
                shots[0].sfx = "whoosh"
            scenes.append(Scene(page=p.number, shots=shots))
        scenes[0].shots[0].narration = f"Pages {pages[0].number} to {pages[-1].number}."
        return ClipScript(title=self.title, hook=f"{self.title}. Watch this.", mood="tense",
                          outro="What happens next?", scenes=scenes)
