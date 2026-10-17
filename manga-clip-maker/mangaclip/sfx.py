"""Procedurally synthesized sound effects and mood music beds.

Everything is generated with numpy, so there are no audio assets to license or
download. Drop your own WAV files into a folder and pass --sfx-dir to override
any effect by name (e.g. impact.wav).
"""

from __future__ import annotations

import os

import numpy as np

SR = 44100
_rng = np.random.default_rng(7)


def _t(seconds: float) -> np.ndarray:
    return np.arange(int(seconds * SR)) / SR


def _noise(seconds: float) -> np.ndarray:
    return _rng.standard_normal(int(seconds * SR)).astype(np.float32)


def _lowpass(x: np.ndarray, cutoff) -> np.ndarray:
    """One-pole low-pass; `cutoff` may be a scalar or a per-sample array (Hz)."""
    cutoff = np.broadcast_to(np.asarray(cutoff, dtype=np.float64), x.shape)
    a = 1.0 - np.exp(-2 * np.pi * cutoff / SR)
    y = np.empty_like(x)
    acc = 0.0
    for i in range(len(x)):  # small buffers only; fine in pure python for SFX
        acc += a[i] * (x[i] - acc)
        y[i] = acc
    return y


def _lowpass_fast(x: np.ndarray, cutoff: float) -> np.ndarray:
    """Fixed-cutoff low-pass via FFT brick wall with a soft knee (for long buffers)."""
    spec = np.fft.rfft(x)
    f = np.fft.rfftfreq(len(x), 1 / SR)
    spec *= 1 / (1 + (f / cutoff) ** 4)
    return np.fft.irfft(spec, n=len(x)).astype(np.float32)


def _norm(x: np.ndarray, peak: float = 0.9) -> np.ndarray:
    m = np.max(np.abs(x)) or 1.0
    return (x / m * peak).astype(np.float32)


def _env(n: int, attack: float, decay: float) -> np.ndarray:
    t = np.arange(n) / SR
    return np.minimum(t / max(attack, 1e-4), 1.0) * np.exp(-t / decay)


def whoosh(d: float = 0.6) -> np.ndarray:
    n = int(d * SR)
    t = np.linspace(0, 1, n)
    env = np.sin(np.pi * t) ** 2
    cutoff = 300 + 3500 * np.sin(np.pi * t) ** 3
    return _norm(_lowpass(_noise(d), cutoff) * env, 0.7)


def impact(d: float = 1.2) -> np.ndarray:
    t = _t(d)
    freq = 40 + 90 * np.exp(-t * 18)
    body = np.sin(2 * np.pi * np.cumsum(freq) / SR) * np.exp(-t * 3.5)
    click = _lowpass_fast(_noise(d), 2500) * np.exp(-t * 40)
    return _norm(body + 0.6 * click)


def punch(d: float = 0.35) -> np.ndarray:
    t = _t(d)
    thump = np.sin(2 * np.pi * (70 + 60 * np.exp(-t * 30)) * t) * np.exp(-t * 14)
    snap_ = _lowpass_fast(_noise(d), 5000) * np.exp(-t * 60)
    return _norm(thump + 0.8 * snap_)


def slash(d: float = 0.4) -> np.ndarray:
    n = int(d * SR)
    t = np.linspace(0, 1, n)
    hp = _noise(d) - _lowpass(_noise(d), 2000 + 6000 * t)
    shing = np.sin(2 * np.pi * 3200 * _t(d)) * np.exp(-_t(d) * 9) * 0.25
    return _norm(hp * np.sin(np.pi * t) ** 0.5 * np.exp(-t * 3) + shing, 0.6)


def explosion(d: float = 2.2) -> np.ndarray:
    t = _t(d)
    rumble = _lowpass_fast(_noise(d), 180) * _env(len(t), 0.01, 0.7)
    crack = _lowpass_fast(_noise(d), 3000) * _env(len(t), 0.002, 0.12)
    boom = np.sin(2 * np.pi * (35 + 50 * np.exp(-t * 6)) * t) * np.exp(-t * 2)
    return _norm(rumble * 2 + crack + boom)


def heartbeat(d: float = 1.6, bpm: float = 70) -> np.ndarray:
    out = np.zeros(int(d * SR), dtype=np.float32)
    beat = punch(0.25) * 0.9
    period = 60 / bpm
    for start in np.arange(0, d - 0.3, period):
        for off, g in ((0.0, 1.0), (0.22, 0.6)):
            i = int((start + off) * SR)
            seg = _lowpass_fast(beat, 150) * g
            out[i:i + len(seg)] += seg[:len(out) - i]
    return _norm(out, 0.9)


def sting(d: float = 1.8) -> np.ndarray:
    """Dramatic minor-chord orchestral-ish stab."""
    t = _t(d)
    out = np.zeros_like(t)
    for f in (110, 130.81, 164.81, 220, 261.63):  # A minor
        for k in range(1, 5):
            out += np.sin(2 * np.pi * f * k * t + k) / k ** 1.3
    out *= _env(len(t), 0.015, 0.6)
    return _norm(out + 0.3 * impact(d)[:len(t)], 0.85)


def chime(d: float = 1.5) -> np.ndarray:
    t = _t(d)
    out = np.zeros_like(t)
    for i, f in enumerate((1318.5, 1567.98, 1975.53, 2637.0)):
        start = int(i * 0.07 * SR)
        tt = t[:len(t) - start]
        out[start:] += np.sin(2 * np.pi * f * tt) * np.exp(-tt * 4)
    return _norm(out, 0.45)


def boing(d: float = 0.7) -> np.ndarray:
    t = _t(d)
    freq = 220 + 120 * np.sin(2 * np.pi * 9 * t) * np.exp(-t * 3) + 150 * t
    return _norm(np.sin(2 * np.pi * np.cumsum(freq) / SR) * np.exp(-t * 4), 0.6)


def rumble(d: float = 2.5) -> np.ndarray:
    n = int(d * SR)
    t = np.linspace(0, 1, n)
    return _norm(_lowpass_fast(_noise(d), 90) * np.sin(np.pi * t), 0.9)


def gasp(d: float = 0.5) -> np.ndarray:
    n = int(d * SR)
    t = np.linspace(0, 1, n)
    breath = _noise(d) - _lowpass_fast(_noise(d), 900)
    return _norm(_lowpass_fast(breath, 4000) * np.sin(np.pi * t ** 0.6) ** 2, 0.35)


EFFECTS = {
    "whoosh": whoosh, "impact": impact, "punch": punch, "slash": slash,
    "explosion": explosion, "heartbeat": heartbeat, "sting": sting, "chime": chime,
    "boing": boing, "rumble": rumble, "gasp": gasp,
}

_cache: dict[str, np.ndarray] = {}


def get_sfx(name: str, sfx_dir: str | None = None) -> np.ndarray | None:
    if not name or name == "none":
        return None
    if sfx_dir:
        for ext in (".wav", ".mp3", ".ogg"):
            path = os.path.join(sfx_dir, name + ext)
            if os.path.exists(path):
                from .audio import load_audio
                return load_audio(path)
    if name not in _cache:
        fn = EFFECTS.get(name)
        if fn is None:
            return None
        _cache[name] = fn()
    return _cache[name]


# --------------------------------------------------------------------------- music

# (root Hz, chord intervals in semitones, progression degrees, tempo bpm, brightness)
_MOOD_MUSIC = {
    "tense":      (55.0, [0, 3, 7], [0, 0, 1, 0], 70, 600),
    "action":     (55.0, [0, 3, 7], [0, 8, 10, 7], 140, 1400),
    "sad":        (58.27, [0, 3, 7, 10], [0, 8, 3, 10], 60, 700),
    "comedic":    (65.41, [0, 4, 7], [0, 5, 7, 5], 120, 2200),
    "mysterious": (51.91, [0, 3, 6], [0, 1, 0, 6], 60, 500),
    "epic":       (55.0, [0, 3, 7], [0, 8, 3, 10], 90, 1200),
    "romantic":   (65.41, [0, 4, 7, 11], [0, 9, 5, 7], 70, 1500),
    "calm":       (65.41, [0, 4, 7, 14], [0, 5, 9, 7], 66, 1000),
}


def music_bed(mood: str, seconds: float) -> np.ndarray:
    """A soft synth pad (plus a pulse for faster moods) looping through a progression."""
    root, chord, prog, bpm, bright = _MOOD_MUSIC.get(mood, _MOOD_MUSIC["tense"])
    total = int(seconds * SR)
    bar = 4 * 60 / bpm
    bar_n = int(bar * SR)
    out = np.zeros(total + bar_n, dtype=np.float32)
    t = np.arange(bar_n) / SR
    fade = np.minimum(1, np.minimum(t, bar - t) / 0.35).astype(np.float32)
    for b in range(int(np.ceil(seconds / bar))):
        degree = prog[b % len(prog)]
        seg = np.zeros(bar_n, dtype=np.float32)
        for iv in chord:
            f = root * 2 ** ((degree + iv) / 12) * 2
            for det in (-0.12, 0.12):  # detuned pair for width
                seg += np.sin(2 * np.pi * (f + det) * t) * 0.5
                seg += np.sin(2 * np.pi * (f * 2 + det) * t) * 0.12
        bass_f = root * 2 ** (degree / 12)
        if bpm >= 110:  # driving eighth-note bass pulse
            beat = 60 / bpm / 2
            pulse = np.exp(-((t % beat) / beat) * 6)
            seg += np.sin(2 * np.pi * bass_f * t) * pulse * 2.0
        else:
            seg += np.sin(2 * np.pi * bass_f * t) * 1.2
        out[b * bar_n:(b + 1) * bar_n] += seg * fade
    out = _lowpass_fast(out[:total], bright)
    # Gentle tremolo keeps the pad from feeling static.
    tt = np.arange(total) / SR
    out *= 0.85 + 0.15 * np.sin(2 * np.pi * 0.25 * tt)
    return _norm(out, 0.5)
