"""Audio I/O and mixing helpers (mono float32 at 44.1 kHz)."""

from __future__ import annotations

import subprocess
import wave

import numpy as np

from .sfx import SR


def load_audio(path: str) -> np.ndarray:
    """Decode any audio file ffmpeg understands into mono float32 at SR."""
    raw = subprocess.run(
        ["ffmpeg", "-v", "error", "-i", path, "-f", "f32le", "-ac", "1", "-ar", str(SR), "-"],
        check=True, capture_output=True).stdout
    return np.frombuffer(raw, dtype=np.float32).copy()


def write_wav(path: str, audio: np.ndarray) -> None:
    pcm = (np.clip(audio, -1, 1) * 32767).astype("<i2")
    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())


def trim_silence(x: np.ndarray, threshold: float = 0.01) -> np.ndarray:
    idx = np.flatnonzero(np.abs(x) > threshold)
    if len(idx) == 0:
        return x[:0]
    pad = int(0.03 * SR)
    return x[max(0, idx[0] - pad):idx[-1] + pad]


def add(track: np.ndarray, clip: np.ndarray, at_seconds: float, gain: float = 1.0) -> None:
    i = int(at_seconds * SR)
    if i >= len(track) or clip is None:
        return
    seg = clip[:len(track) - i]
    track[i:i + len(seg)] += seg * gain


def duck_envelope(voice: np.ndarray, floor: float = 0.35, release: float = 0.4) -> np.ndarray:
    """Gain curve that dips the music while the narrator is talking."""
    hop = 512
    n = max(1, -(-len(voice) // hop))
    rms = np.array([np.sqrt(np.mean(voice[i * hop:(i + 1) * hop] ** 2) + 1e-12) for i in range(n)])
    active = (rms > 0.01).astype(np.float32)
    # Smooth: fast attack, slower release.
    k = max(1, int(release * SR / hop))
    smooth = np.convolve(active, np.ones(k) / k, mode="same")
    smooth = np.maximum(smooth, active)
    gain = 1 - (1 - floor) * np.clip(smooth, 0, 1)
    return np.repeat(gain, hop)[:len(voice)].astype(np.float32)


def master(mix: np.ndarray) -> np.ndarray:
    """Soft-clip limiter and normalize to a safe peak."""
    peak = np.max(np.abs(mix)) or 1.0
    mix = mix / peak * 1.2
    mix = np.tanh(mix) / np.tanh(1.2)
    return (mix * 0.92).astype(np.float32)
