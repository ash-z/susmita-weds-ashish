"""Turn a ClipScript into a video: camera moves over panels, captions, narration, SFX, music."""

from __future__ import annotations

import glob
import logging
import os
import subprocess
import tempfile
from dataclasses import dataclass

import numpy as np
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont

from . import audio as A
from .pdf import Page
from .script import ClipScript
from .music import MusicLibrary, MusicPolicy, Track, render_cues
from .sfx import SR, get_sfx
from .tts import TTS

log = logging.getLogger(__name__)

FORMATS = {"vertical": (1080, 1920), "landscape": (1920, 1080), "square": (1080, 1080)}
FONT_CANDIDATES = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
    "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
    "C:/Windows/Fonts/arialbd.ttf",
]
CJK_FONT_GLOBS = ["/usr/share/fonts/**/NotoSansCJK*Bold*", "/usr/share/fonts/**/*CJK*",
                  "/usr/share/fonts/**/wqy*", "/usr/share/fonts/**/*japanese*"]


def find_font(text_sample: str = "") -> str | None:
    needs_cjk = any(ord(c) > 0x2E80 for c in text_sample)
    if needs_cjk:
        for pattern in CJK_FONT_GLOBS:
            hits = glob.glob(pattern, recursive=True)
            if hits:
                return hits[0]
    for path in FONT_CANDIDATES:
        if os.path.exists(path):
            return path
    return None


# --------------------------------------------------------------------------- timeline

Cam = tuple[float, float, float]  # center x, center y, width (world pixels)


@dataclass
class Segment:
    world: int  # index into the per-page world images
    start: Cam
    end: Cam
    duration: float
    caption: str = ""
    title: str = ""  # large centered text (title / outro cards)
    dim: float = 0.0  # 0..1 darkening (for title cards)
    fade_in: float = 0.0
    fade_out: float = 0.0
    shake: float = 0.0  # seconds of camera shake at segment start
    ease: bool = True


class World:
    """A page placed on a blurred, darkened copy of itself so the camera can roam freely."""

    def __init__(self, page: Image.Image, aspect: float):
        pw, ph = page.size
        self.aspect = aspect
        margin = int(max(pw, ph) * 0.5)
        W, H = pw + 2 * margin, ph + 2 * margin
        bg = page.copy()
        scale = max(W / pw, H / ph)
        bg = bg.resize((int(pw * scale) + 1, int(ph * scale) + 1), Image.BILINEAR)
        bg = bg.crop((0, 0, W, H)).filter(ImageFilter.GaussianBlur(40))
        bg = ImageEnhance.Brightness(bg).enhance(0.35)
        bg.paste(page, (margin, margin))
        self.image = bg
        self.ox, self.oy, self.pw, self.ph = margin, margin, pw, ph

    def cam_for_box(self, box, pad: float = 1.08) -> Cam:
        x0, y0, x1, y1 = box
        bw, bh = (x1 - x0) * self.pw, (y1 - y0) * self.ph
        cx = self.ox + (x0 + x1) / 2 * self.pw
        cy = self.oy + (y0 + y1) / 2 * self.ph
        w = max(bw, bh * self.aspect) * pad
        return self.clamp((cx, cy, w))

    def full(self) -> Cam:
        return self.cam_for_box((0, 0, 1, 1), pad=1.04)

    def clamp(self, cam: Cam) -> Cam:
        cx, cy, w = cam
        W, H = self.image.size
        w = min(max(w, 200), W, H * self.aspect)
        h = w / self.aspect
        cx = min(max(cx, w / 2), W - w / 2)
        cy = min(max(cy, h / 2), H - h / 2)
        return cx, cy, w


def _ease(t: float) -> float:
    return t * t * (3 - 2 * t)


def _wrap(draw: ImageDraw.ImageDraw, text: str, font, max_w: int) -> list[str]:
    words = text.split()
    if len(words) <= 1 and draw.textlength(text, font=font) > max_w:
        # No spaces (e.g. Japanese): wrap by character.
        words, joiner = list(text), ""
    else:
        joiner = " "
    lines, cur = [], ""
    for wd in words:
        trial = (cur + joiner + wd) if cur else wd
        if draw.textlength(trial, font=font) <= max_w:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = wd
    if cur:
        lines.append(cur)
    return lines


class Renderer:
    def __init__(self, fmt: str = "vertical", fps: int = 30, captions: bool = True,
                 tts: TTS | None = None, sfx_dir: str | None = None, music: bool = True,
                 music_volume: float = 0.22, sfx_volume: float = 0.7,
                 music_library: MusicLibrary | None = None,
                 music_policy: MusicPolicy | None = None):
        self.size = FORMATS[fmt]
        self.aspect = self.size[0] / self.size[1]
        self.fps = fps
        self.captions = captions
        self.tts = tts or TTS()
        self.sfx_dir = sfx_dir
        self.music = music
        self.music_volume = music_volume
        self.sfx_volume = sfx_volume
        self.music_library = music_library
        self.music_policy = music_policy or MusicPolicy()
        self.last_music: list[Track] = []  # tracks used by the most recent render

    # ---------------------------------------------------------------- build

    def build(self, script: ClipScript, pages: dict[int, Page]):
        worlds = [World(pages[s.page].image, self.aspect) for s in script.scenes]
        segs: list[Segment] = []
        voice_cues: list[tuple[float, np.ndarray]] = []
        sfx_cues: list[tuple[float, str]] = []
        music_cues: list[tuple[float, float, str, int]] = []  # start, end, mood, energy
        hits: list[float] = []  # emphasis moments: music dips so the impact lands
        t = 0.0

        def speak(text: str, tone: str = "neutral") -> np.ndarray:
            return self.tts.speak(text, tone) if text else np.zeros(0, np.float32)

        frame_tone = {"action": "excited", "epic": "excited", "comedic": "comedic",
                      "sad": "sad", "romantic": "neutral", "calm": "neutral"}.get(script.mood, "tense")

        # Title card over the first page.
        hook = speak(script.hook, frame_tone)
        full0 = worlds[0].full()
        zoom_in = (full0[0], full0[1], full0[2] * 0.94)
        dur = max(2.6, len(hook) / SR + 0.7)
        segs.append(Segment(0, full0, zoom_in, dur, caption=script.hook if self.captions else "",
                            title=script.title, dim=0.55, fade_in=0.3, ease=False))
        voice_cues.append((t + 0.35, hook))
        sfx_cues.append((t, "sting"))
        t += dur
        cam = zoom_in

        for wi, scene in enumerate(script.scenes):
            world = worlds[wi]
            scene_start = 0.0 if wi == 0 else t
            if wi > 0:
                # New page: quick establishing look at the whole page.
                cam = world.full()
                est = 0.9
                segs.append(Segment(wi, cam, (cam[0], cam[1], cam[2] * 0.97), est,
                                    fade_in=0.25, ease=False))
                sfx_cues.append((t, "whoosh"))
                t += est
                cam = (cam[0], cam[1], cam[2] * 0.97)
            for shot in scene.shots:
                target = world.cam_for_box(shot.box)
                move = 0.55
                segs.append(Segment(wi, cam, target, move))
                if shot.sfx in ("whoosh", "slash"):
                    sfx_cues.append((t, shot.sfx))
                t += move
                voice = speak(shot.narration, shot.tone)
                hold = max(1.5 if shot.narration else 1.2, len(voice) / SR + 0.35)
                if shot.emphasis:
                    hold = max(hold, 1.8)
                zoom = 0.88 if shot.emphasis else 0.96
                end = world.clamp((target[0], target[1], target[2] * zoom))
                segs.append(Segment(wi, target, end, hold,
                                    caption=shot.narration if self.captions else "",
                                    shake=0.35 if shot.emphasis else 0.0, ease=False))
                if shot.sfx not in ("none", "whoosh", "slash"):
                    sfx_cues.append((t, shot.sfx))
                if shot.emphasis:
                    hits.append(t)
                voice_cues.append((t + 0.1, voice))
                t += hold
                cam = end
            if wi < len(script.scenes) - 1:
                segs[-1].fade_out = 0.25
            music_cues.append((scene_start, t, scene.music_mood or script.mood,
                               scene.music_energy))

        # Outro over the last page.
        outro = speak(script.outro, frame_tone)
        lw = len(worlds) - 1
        full = worlds[lw].full()
        segs.append(Segment(lw, cam, full, 0.7))
        t += 0.7
        dur = max(2.2, len(outro) / SR + 0.9)
        segs.append(Segment(lw, full, (full[0], full[1], full[2] * 1.03), dur,
                            caption=script.outro if self.captions else "",
                            dim=0.45, fade_out=0.6, ease=False))
        voice_cues.append((t + 0.2, outro))
        sfx_cues.append((t, "rumble" if script.mood in ("tense", "mysterious", "epic") else "chime"))
        t += dur
        last = music_cues[-1]
        music_cues[-1] = (last[0], t, last[2], last[3])  # last scene's music carries the outro
        return worlds, segs, voice_cues, sfx_cues, music_cues, hits, t

    # ---------------------------------------------------------------- audio

    def mix_audio(self, total: float, voice_cues, sfx_cues, music_cues, hits) -> np.ndarray:
        n = int(total * SR) + SR
        voice = np.zeros(n, np.float32)
        for at, clip in voice_cues:
            A.add(voice, clip, at)
        fx = np.zeros(n, np.float32)
        for at, name in sfx_cues:
            A.add(fx, get_sfx(name, self.sfx_dir), at)
        mix = voice + fx * self.sfx_volume
        self.last_music = []
        if self.music:
            bed, self.last_music = render_cues(music_cues, n / SR, self.music_library,
                                               self.music_policy)
            fade = np.ones(n, np.float32)
            k = int(1.5 * SR)
            fade[:k] = np.linspace(0, 1, k)
            fade[-k:] = np.linspace(1, 0, k)
            for at in hits:  # brief dip under big impacts
                i, d = int(at * SR), int(0.6 * SR)
                dip = 1 - 0.7 * np.sin(np.linspace(0, np.pi, d)) ** 0.5
                fade[i:i + d] *= dip[:max(0, min(d, n - i))]
            mix += bed[:n] * self.music_volume * A.duck_envelope(voice) * fade
        return A.master(mix)[:int(total * SR)]

    # ---------------------------------------------------------------- video

    def _frame(self, world: World, cam: Cam, seg: Segment, local_t: float,
               fonts: dict) -> Image.Image:
        W, H = self.size
        cx, cy, w = cam
        h = w / self.aspect
        frame = world.image.resize((W, H), Image.BILINEAR,
                                   box=(cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2))
        alpha = 1.0
        if seg.fade_in and local_t < seg.fade_in:
            alpha = local_t / seg.fade_in
        if seg.fade_out and local_t > seg.duration - seg.fade_out:
            alpha = min(alpha, (seg.duration - local_t) / seg.fade_out)
        dim = seg.dim
        if dim or alpha < 1:
            frame = ImageEnhance.Brightness(frame).enhance(max(0.0, (1 - dim) * alpha))
        if not (seg.title or seg.caption):
            return frame
        draw = ImageDraw.Draw(frame)
        text_alpha = min(1.0, local_t / 0.2) * alpha
        if text_alpha <= 0.02:
            return frame
        fill = (255, 255, 255)
        if seg.title:
            font = fonts["title"]
            lines = _wrap(draw, seg.title.upper(), font, int(W * 0.86))
            lh = font.size * 1.15
            y = H * 0.40 - lh * len(lines) / 2
            for line in lines:
                tw = draw.textlength(line, font=font)
                draw.text(((W - tw) / 2, y), line, font=font, fill=(255, 214, 64),
                          stroke_width=max(2, font.size // 14), stroke_fill=(0, 0, 0))
                y += lh
        if seg.caption:
            font = fonts["caption"]
            lines = _wrap(draw, seg.caption, font, int(W * 0.84))
            lh = font.size * 1.25
            base = H * (0.78 if H > W else 0.86)
            y = base - lh * len(lines) / 2
            for line in lines:
                tw = draw.textlength(line, font=font)
                draw.text(((W - tw) / 2, y), line, font=font, fill=fill,
                          stroke_width=max(2, font.size // 10), stroke_fill=(0, 0, 0))
                y += lh
        return frame

    def render(self, script: ClipScript, pages: dict[int, Page], out_path: str) -> str:
        worlds, segs, voice_cues, sfx_cues, music_cues, hits, total = self.build(script, pages)
        n_frames = int(round(total * self.fps))
        total = n_frames / self.fps
        log.info("Rendering %s: %.1fs, %d frames", out_path, total, n_frames)

        sample = script.title + script.hook + "".join(
            sh.narration for sc in script.scenes for sh in sc.shots)
        font_path = find_font(sample)
        W, H = self.size
        unit = min(W, H)

        def font(size):
            return ImageFont.truetype(font_path, size) if font_path else ImageFont.load_default(size)

        fonts = {"title": font(int(unit * 0.085)), "caption": font(int(unit * 0.052))}

        tmp = tempfile.mkdtemp(prefix="mangaclip-")
        wav = os.path.join(tmp, "mix.wav")
        A.write_wav(wav, self.mix_audio(total, voice_cues, sfx_cues, music_cues, hits))

        cmd = ["ffmpeg", "-y", "-v", "error",
               "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(self.fps),
               "-i", "-", "-i", wav,
               "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p",
               "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", "-shortest", out_path]
        proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
        rng = np.random.default_rng(1)
        seg_i, seg_start = 0, 0.0
        try:
            for f in range(n_frames):
                t = f / self.fps
                while seg_i < len(segs) - 1 and t >= seg_start + segs[seg_i].duration:
                    seg_start += segs[seg_i].duration
                    seg_i += 1
                seg = segs[seg_i]
                lt = min(t - seg_start, seg.duration)
                p = lt / seg.duration if seg.duration else 1.0
                p = _ease(p) if seg.ease else p
                cam = tuple(a + (b - a) * p for a, b in zip(seg.start, seg.end))
                if seg.shake and lt < seg.shake:
                    amp = cam[2] * 0.012 * (1 - lt / seg.shake)
                    cam = (cam[0] + rng.uniform(-amp, amp), cam[1] + rng.uniform(-amp, amp), cam[2])
                world = worlds[seg.world]
                frame = self._frame(world, world.clamp(cam), seg, lt, fonts)
                proc.stdin.write(frame.tobytes())
        finally:
            proc.stdin.close()
            proc.wait()
        if proc.returncode != 0:
            raise RuntimeError(f"ffmpeg failed with code {proc.returncode}")
        return out_path
