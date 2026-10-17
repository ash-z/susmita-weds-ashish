"""Text-to-speech engines.

  edge    - Microsoft Edge neural voices via `edge-tts` (free, needs internet). Default.
  gtts    - Google Translate TTS via `gTTS` (free, needs internet).
  pyttsx3 - fully offline system voices (espeak / SAPI / NSSpeech).
  silent  - no audio; reserves time based on word count (for testing the pipeline).
"""

from __future__ import annotations

import asyncio
import hashlib
import os
import tempfile

import numpy as np

from .audio import load_audio, trim_silence
from .sfx import SR


class TTS:
    def __init__(self, engine: str = "edge", voice: str | None = None, rate: str = "+8%",
                 cache_dir: str | None = None, language: str = "en"):
        self.engine = engine
        self.voice = voice or "en-US-GuyNeural"
        self.rate = rate
        self.language = language
        self.cache_dir = cache_dir or os.path.join(tempfile.gettempdir(), "mangaclip-tts")
        os.makedirs(self.cache_dir, exist_ok=True)

    def speak(self, text: str) -> np.ndarray:
        text = text.strip()
        if not text:
            return np.zeros(0, dtype=np.float32)
        if self.engine == "silent":
            words = len(text.split())
            return np.zeros(int(SR * (0.4 + words / 2.7)), dtype=np.float32)
        key = hashlib.sha1(f"{self.engine}|{self.voice}|{self.rate}|{text}".encode()).hexdigest()
        path = os.path.join(self.cache_dir, key + (".wav" if self.engine == "pyttsx3" else ".mp3"))
        if not os.path.exists(path) or os.path.getsize(path) == 0:
            getattr(self, f"_{self.engine}")(text, path)
        return trim_silence(load_audio(path))

    def _edge(self, text: str, path: str) -> None:
        import edge_tts

        proxy = os.environ.get("HTTPS_PROXY") or os.environ.get("https_proxy")
        comm = edge_tts.Communicate(text, self.voice, rate=self.rate, proxy=proxy)
        asyncio.run(comm.save(path))

    def _gtts(self, text: str, path: str) -> None:
        from gtts import gTTS

        gTTS(text=text, lang=self.language).save(path)

    def _pyttsx3(self, text: str, path: str) -> None:
        import pyttsx3

        engine = pyttsx3.init()
        engine.save_to_file(text, path)
        engine.runAndWait()
