"""Background music: a license-aware track library matched to each scene's mood.

Copyrighted music (anime OSTs, pop songs...) gets clips claimed, muted or blocked by
Content ID on YouTube/TikTok/Instagram. So every track in the library must declare its
license, and only tracks that are safe for the intended use are picked. When nothing
fits, we fall back to the built-in synthesized music, which is always copyright-free.

Library layout (any folder):

    music/
      library.json        # created by `python -m mangaclip.music init music/`
      tense/dark_pulse.mp3  # optional: a mood-named subfolder pre-tags the mood
      ...

library.json entries:
    {"file": "tense/dark_pulse.mp3", "title": "Dark Pulse", "artist": "Someone",
     "license": "cc-by", "source": "https://...", "moods": ["tense", "mysterious"],
     "energy": 3, "bpm": 92, "start": 0.0, "attribution": "Dark Pulse by Someone (CC BY 4.0)"}
"""

from __future__ import annotations

import argparse
import json
import logging
import os
from dataclasses import asdict, dataclass, field

import numpy as np

from .script import MOODS
from .sfx import SR

log = logging.getLogger(__name__)

AUDIO_EXTS = (".mp3", ".wav", ".ogg", ".flac", ".m4a", ".aac", ".opus")

# license -> (usable at all, ok for monetized/commercial use, attribution required)
LICENSES = {
    "cc0": (True, True, False),
    "public-domain": (True, True, False),
    "cc-by": (True, True, True),
    "cc-by-sa": (True, True, True),
    "cc-by-nc": (True, False, True),
    "cc-by-nc-sa": (True, False, True),
    "cc-by-nd": (True, True, True),
    "cc-by-nc-nd": (True, False, True),
    "pixabay": (True, True, False),  # Pixabay Content License
    "youtube-audio-library": (True, True, False),  # some tracks need credit: set "attribution"
    "royalty-free": (True, True, False),  # a license you bought (Epidemic, Artlist, ...)
    "owned": (True, True, False),  # your own composition
    "copyrighted": (False, False, False),
    "unknown": (False, False, False),
}

# Moods that can stand in for each other when there is no exact match.
RELATED = {
    "tense": ["mysterious", "action"], "action": ["epic", "tense"],
    "sad": ["romantic", "calm"], "comedic": ["calm"], "mysterious": ["tense", "calm"],
    "epic": ["action", "tense"], "romantic": ["calm", "sad"], "calm": ["romantic", "sad"],
}


@dataclass
class Track:
    file: str
    title: str = ""
    artist: str = ""
    license: str = "unknown"
    source: str = ""
    moods: list[str] = field(default_factory=list)
    energy: int = 3  # 1 (ambient) .. 5 (driving)
    bpm: float = 0.0
    start: float = 0.0  # skip a long intro
    attribution: str = ""
    duration: float = 0.0

    @property
    def needs_credit(self) -> bool:
        return bool(self.attribution) or LICENSES.get(self.license, (0, 0, 0))[2]

    def credit_line(self) -> str:
        if self.attribution:
            return self.attribution
        who = f'"{self.title or os.path.basename(self.file)}"' + (f" by {self.artist}" if self.artist else "")
        if not LICENSES.get(self.license, LICENSES["unknown"])[0]:
            return f"{who} ({self.license}; NOT cleared for publishing)"
        lic = self.license.upper().replace("CC-", "CC ").replace("-", " ")
        return f"{who}, licensed under {lic}" + (f" ({self.source})" if self.source else "")


@dataclass
class MusicPolicy:
    commercial: bool = True  # monetized channel -> no NonCommercial licenses
    allow_unlicensed: bool = False  # private previews only; will be claimed if uploaded

    def allows(self, t: Track) -> tuple[bool, str]:
        usable, commercial_ok, _ = LICENSES.get(t.license, LICENSES["unknown"])
        if not usable:
            if self.allow_unlicensed:
                return True, "unlicensed (allowed for private preview)"
            return False, f"license '{t.license}' is not safe to publish"
        if self.commercial and not commercial_ok:
            return False, f"license '{t.license}' forbids commercial/monetized use"
        return True, "ok"


class MusicLibrary:
    def __init__(self, root: str, tracks: list[Track]):
        self.root = root
        self.tracks = tracks

    @classmethod
    def load(cls, root: str) -> "MusicLibrary":
        path = os.path.join(root, "library.json")
        entries = []
        if os.path.exists(path):
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
            entries = data["tracks"] if isinstance(data, dict) else data
        known = {e["file"] for e in entries}
        tracks = [Track(**{k: v for k, v in e.items() if k in Track.__dataclass_fields__})
                  for e in entries]
        for rel in _scan(root):
            if rel not in known:
                tracks.append(Track(file=rel, moods=_folder_moods(rel)))  # license unknown
        for t in tracks:
            t.license = t.license.lower().strip()
            t.moods = [m for m in (x.lower() for x in t.moods) if m in MOODS]
        return cls(root, tracks)

    def path(self, t: Track) -> str:
        return os.path.join(self.root, t.file)

    def pick(self, mood: str, energy: int, policy: MusicPolicy,
             avoid: set[str] = frozenset()) -> Track | None:
        best, best_score = None, -1e9
        for t in self.tracks:
            ok, _ = policy.allows(t)
            if not ok or not os.path.exists(self.path(t)):
                continue
            if mood in t.moods:
                score = 10.0
            elif any(m in t.moods for m in RELATED.get(mood, [])):
                score = 5.0
            elif not t.moods:
                score = 1.0
            else:
                continue
            score -= 1.5 * abs(t.energy - energy)
            score -= 4.0 if t.file in avoid else 0.0
            score -= 0.0 if LICENSES.get(t.license, (0,))[0] else 6.0  # prefer licensed tracks
            if score > best_score:
                best, best_score = t, score
        return best

    def report(self, policy: MusicPolicy) -> list[str]:
        lines = []
        for t in self.tracks:
            ok, why = policy.allows(t)
            mark = "OK  " if ok else "SKIP"
            lines.append(f"{mark} {t.file}  [{t.license}] moods={','.join(t.moods) or '-'} "
                         f"energy={t.energy}" + ("" if ok else f"  <- {why}"))
        return lines


def _scan(root: str) -> list[str]:
    out = []
    for dirpath, _, files in os.walk(root):
        for f in files:
            if f.lower().endswith(AUDIO_EXTS):
                out.append(os.path.relpath(os.path.join(dirpath, f), root).replace(os.sep, "/"))
    return sorted(out)


def _folder_moods(rel: str) -> list[str]:
    return [p.lower() for p in rel.split("/")[:-1] if p.lower() in MOODS]


# --------------------------------------------------------------------------- analysis

def analyze_audio(x: np.ndarray) -> dict:
    """Estimate energy (1-5) from how often the track hits (onsets/sec), plus a rough tempo."""
    if len(x) < SR:
        return {"energy": 3, "bpm": 0.0, "duration": len(x) / SR}
    hop = 2048  # ~46 ms: long enough to smooth out low-frequency ripple and beating
    n = len(x) // hop
    rms = np.sqrt((x[:n * hop].reshape(n, hop) ** 2).mean(axis=1) + 1e-12)
    db = 20 * np.log10(rms + 1e-9)
    rise = np.maximum(np.diff(db), 0)
    onset_rate = float((rise > 3).sum()) / (len(x) / SR)  # loudness jumps of 3 dB+
    energy = 1 + int(np.searchsorted([0.3, 1.0, 2.0, 3.0], onset_rate))
    # Tempo from the autocorrelation of the onset envelope (60-180 bpm).
    env = rise - rise.mean()
    ac = np.correlate(env, env, mode="full")[len(env) - 1:]
    fps = SR / hop
    lo, hi = int(fps * 60 / 180), int(fps * 60 / 60)
    bpm = 60 * fps / (lo + int(np.argmax(ac[lo:hi]))) if onset_rate > 0.3 and hi < len(ac) else 0.0
    return {"energy": energy, "bpm": round(float(bpm), 1), "duration": round(len(x) / SR, 1)}


def init_library(root: str) -> str:
    """Create/refresh library.json: keep existing entries, add and analyze new files."""
    from .audio import load_audio

    lib = MusicLibrary.load(root)
    for t in lib.tracks:
        if not t.duration:
            info = analyze_audio(load_audio(lib.path(t)))
            t.energy, t.bpm, t.duration = info["energy"], info["bpm"], info["duration"]
        if not t.title:
            t.title = os.path.splitext(os.path.basename(t.file))[0].replace("_", " ")
    path = os.path.join(root, "library.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump({"tracks": [asdict(t) for t in lib.tracks]}, f, indent=2, ensure_ascii=False)
    return path


# --------------------------------------------------------------------------- playback

def render_cues(cues: list[tuple[float, float, str, int]], total: float,
                library: MusicLibrary | None, policy: MusicPolicy,
                xfade: float = 1.5) -> tuple[np.ndarray, list[Track]]:
    """Build the music track from (start, end, mood, energy) cues.

    Consecutive cues with the same mood share one continuous track; mood changes
    crossfade into a newly picked track. Returns the audio and the tracks used.
    """
    from .audio import load_audio
    from .sfx import music_bed

    n = int(total * SR)
    out = np.zeros(n, np.float32)
    used: list[Track] = []
    merged: list[list] = []
    for c in cues:
        if merged and merged[-1][2] == c[2]:
            merged[-1][1] = c[1]
        else:
            merged.append(list(c))
    xn = int(xfade * SR)
    for i, (start, end, mood, energy) in enumerate(merged):
        a = max(0, int(start * SR) - (xn if i else 0))
        b = min(n, int(end * SR) + (xn if i < len(merged) - 1 else 0))
        length = b - a
        track = library.pick(mood, energy, policy, {t.file for t in used}) if library else None
        if track:
            audio = load_audio(library.path(track))[int(track.start * SR):]
            audio = audio / (np.max(np.abs(audio)) or 1.0) * 0.5
            if track not in used:
                used.append(track)
            log.info("Music %.1f-%.1fs (%s): %s [%s]", start, end, mood, track.file, track.license)
        else:
            audio = music_bed(mood, length / SR + 0.1)
        if len(audio) < length:  # loop with a short crossfade
            reps = int(np.ceil(length / max(len(audio) - xn, 1))) + 1
            looped = audio.copy()
            ramp = np.linspace(0, 1, min(xn, len(audio)), dtype=np.float32)
            for _ in range(reps):
                k = len(ramp)
                looped[-k:] = looped[-k:] * (1 - ramp) + audio[:k] * ramp
                looped = np.concatenate([looped, audio[k:]])
                if len(looped) >= length:
                    break
            audio = looped
        seg = audio[:length].astype(np.float32)
        env = np.ones(length, np.float32)
        k = min(xn, length // 2)
        if i:
            env[:k] = np.linspace(0, 1, k)
        if i < len(merged) - 1:
            env[-k:] = np.linspace(1, 0, k)
        out[a:b] += seg * env
    return out, used


def write_credits(path: str, tracks: list[Track]) -> None:
    lines = ["Music credits (paste into the video description):", ""]
    if tracks:
        lines += [t.credit_line() for t in tracks]
    else:
        lines.append("Original synthesized music (no credit required).")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


# --------------------------------------------------------------------------- CLI

def main(argv: list[str] | None = None) -> None:
    p = argparse.ArgumentParser(prog="python -m mangaclip.music",
                                description="Manage a license-aware music library.")
    sub = p.add_subparsers(dest="cmd", required=True)
    i = sub.add_parser("init", help="create/refresh library.json (analyzes energy and tempo)")
    i.add_argument("dir")
    c = sub.add_parser("check", help="show which tracks are allowed and why")
    c.add_argument("dir")
    c.add_argument("--non-commercial", action="store_true",
                   help="allow NonCommercial licenses (channel is not monetized)")
    a = p.parse_args(argv)
    if a.cmd == "init":
        path = init_library(a.dir)
        print(f"Wrote {path}. Fill in license, source, artist and moods for each track.")
        print(f"Licenses: {', '.join(LICENSES)}.  Moods: {', '.join(MOODS)}.")
    else:
        lib = MusicLibrary.load(a.dir)
        for line in lib.report(MusicPolicy(commercial=not a.non_commercial)):
            print(line)


if __name__ == "__main__":
    main()
