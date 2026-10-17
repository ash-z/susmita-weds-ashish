"""Text-to-speech for the narration.

Engines:
  edge    - Microsoft Edge neural voices via `edge-tts` (free, needs internet). Best quality.
  piper   - Piper neural voices, fully offline after a one-time voice download.
  gtts    - Google Translate TTS via `gTTS` (free, needs internet).
  pyttsx3 - offline system voices (espeak / SAPI / NSSpeech). Robotic.
  silent  - no audio; reserves time based on word count (for testing the pipeline).
  auto    - try edge, then piper, then gtts, then pyttsx3, and use the first that works.

Narration is the heart of a clip, so failures are never silent: if an engine fails we
fall back to the next one with a warning, and if none work we raise.
"""

from __future__ import annotations

import asyncio
import hashlib
import logging
import os
import re
import tempfile
import wave

import numpy as np

from .audio import load_audio, trim_silence
from .sfx import SR

log = logging.getLogger(__name__)

AUTO_ORDER = ["edge", "piper", "gtts", "pyttsx3"]

# Per-tone delivery: (rate change in %, pitch change in Hz, volume change in %).
TONE_PROSODY = {
    "neutral": (0, 0, 0),
    "tense": (-6, -3, 0),
    "excited": (10, 4, 5),
    "whisper": (-10, -4, -25),
    "sad": (-14, -5, -10),
    "comedic": (6, 6, 0),
}

DEFAULT_PIPER_VOICE = "en_US-ryan-high"
LANG_CODES = {"english": "en", "japanese": "ja", "spanish": "es", "french": "fr",
              "german": "de", "portuguese": "pt", "italian": "it", "hindi": "hi",
              "korean": "ko", "chinese": "zh", "indonesian": "id", "russian": "ru"}
PIPER_DIR = os.path.join(os.path.expanduser("~"), ".cache", "mangaclip", "piper")


def _pct(s: str) -> int:
    m = re.fullmatch(r"\s*([+-]?\d+)\s*%?\s*", s or "0")
    return int(m.group(1)) if m else 0


def clean_for_speech(text: str) -> str:
    """Strip things TTS engines read literally or stumble on."""
    text = re.sub(r"[*_#~`|<>\[\]{}]", "", text)
    text = re.sub(r"\([^)]*\)", "", text)  # stage directions in parentheses
    text = text.replace("…", ", ").replace("...", ", ")
    text = re.sub(r"[—–]", ", ", text)
    text = re.sub(r"!{2,}", "!", text)
    text = re.sub(r"\?{2,}", "?", text)
    text = re.sub(r"\s+,", ",", text)
    return re.sub(r"\s{2,}", " ", text).strip(" ,")


class NarrationError(RuntimeError):
    pass


class TTS:
    def __init__(self, engine: str = "auto", voice: str | None = None, rate: str = "+5%",
                 cache_dir: str | None = None, language: str = "en"):
        self.engine = engine
        self.voice = voice
        self.rate = _pct(rate)
        self.language = LANG_CODES.get(language.lower(), language)
        self.cache_dir = cache_dir or os.path.join(tempfile.gettempdir(), "mangaclip-tts")
        os.makedirs(self.cache_dir, exist_ok=True)
        self.engines = AUTO_ORDER[:] if engine == "auto" else [engine]
        self.failed: dict[str, str] = {}  # engine -> error message
        self.used: set[str] = set()
        self._piper_voice = None

    # ---------------------------------------------------------------- public

    def speak(self, text: str, tone: str = "neutral") -> np.ndarray:
        text = clean_for_speech(text)
        if not text:
            return np.zeros(0, dtype=np.float32)
        if self.engine == "silent":
            words = len(text.split())
            return np.zeros(int(SR * (0.4 + words / 2.6)), dtype=np.float32)
        for eng in self.engines:
            if eng in self.failed:
                continue
            try:
                audio = self._speak_with(eng, text, tone)
            except Exception as e:  # any engine failure -> try the next one
                self.failed[eng] = f"{type(e).__name__}: {e}"
                if len(self.engines) > 1:
                    log.warning("TTS engine '%s' failed (%s); trying the next one", eng, e)
                continue
            if len(audio) < SR * 0.1:
                self.failed[eng] = "produced no audio"
                continue
            self.used.add(eng)
            return audio
        details = "; ".join(f"{k}: {v}" for k, v in self.failed.items())
        raise NarrationError(
            "Could not synthesize narration with any voice engine "
            f"({details}). Check your internet connection for edge/gtts, or install an "
            "offline voice: pip install piper-tts (see README).")

    def describe(self) -> str:
        if self.engine == "silent":
            return "silent (no voice)"
        return ", ".join(sorted(self.used)) or "none"

    # ---------------------------------------------------------------- engines

    def _speak_with(self, eng: str, text: str, tone: str) -> np.ndarray:
        rate_d, pitch_d, vol_d = TONE_PROSODY.get(tone, (0, 0, 0))
        voice = self._voice_for(eng)
        key = hashlib.sha1(f"{eng}|{voice}|{self.rate}|{tone}|{text}".encode()).hexdigest()
        ext = ".mp3" if eng in ("edge", "gtts") else ".wav"
        path = os.path.join(self.cache_dir, key + ext)
        if not os.path.exists(path) or os.path.getsize(path) == 0:
            tmp = path + ".part"
            getattr(self, f"_{eng}")(text, tmp, voice, self.rate + rate_d, pitch_d, vol_d)
            os.replace(tmp, path)
        audio = trim_silence(load_audio(path))
        if eng in ("gtts", "pyttsx3") and vol_d:  # engines without native volume control
            audio = audio * (1 + vol_d / 100)
        return audio

    def _voice_for(self, eng: str) -> str | None:
        v = self.voice
        if eng == "edge":
            return v if v and v.endswith("Neural") else "en-US-AndrewMultilingualNeural"
        if eng == "piper":
            if v and (v.endswith(".onnx") or re.fullmatch(r"[a-z]{2,3}_[A-Z]{2}-\w+-\w+", v)):
                return v
            return DEFAULT_PIPER_VOICE
        return v

    def _edge(self, text, path, voice, rate, pitch, vol):
        import edge_tts

        proxy = os.environ.get("HTTPS_PROXY") or os.environ.get("https_proxy")
        comm = edge_tts.Communicate(text, voice, rate=f"{rate:+d}%", pitch=f"{pitch:+d}Hz",
                                    volume=f"{vol:+d}%", proxy=proxy)
        asyncio.run(comm.save(path))

    def _piper(self, text, path, voice, rate, pitch, vol):
        from piper import PiperVoice, SynthesisConfig

        if self._piper_voice is None:
            if voice.endswith(".onnx"):
                model = voice
            else:
                from pathlib import Path

                from piper.download_voices import download_voice

                os.makedirs(PIPER_DIR, exist_ok=True)
                model = os.path.join(PIPER_DIR, voice + ".onnx")
                if not os.path.exists(model):
                    log.warning("Downloading Piper voice %s (one time)", voice)
                    download_voice(voice, Path(PIPER_DIR))
            self._piper_voice = PiperVoice.load(model)
        # Piper has no pitch control; rate maps to phoneme length (smaller = faster).
        cfg = SynthesisConfig(length_scale=1 / (1 + rate / 100), volume=1 + vol / 100)
        with wave.open(path, "wb") as wf:
            self._piper_voice.synthesize_wav(text, wf, syn_config=cfg)

    def _gtts(self, text, path, voice, rate, pitch, vol):
        from gtts import gTTS

        gTTS(text=text, lang=self.language, slow=rate < -10).save(path)

    def _pyttsx3(self, text, path, voice, rate, pitch, vol):
        import pyttsx3

        engine = pyttsx3.init()
        engine.setProperty("rate", int(175 * (1 + rate / 100)))
        if voice:
            engine.setProperty("voice", voice)
        engine.save_to_file(text, path)
        engine.runAndWait()
