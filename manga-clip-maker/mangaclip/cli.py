"""Command line interface: python -m mangaclip input.pdf -o out/"""

from __future__ import annotations

import argparse
import logging

from .pipeline import Options, make_clips
from .render import FORMATS


def main(argv: list[str] | None = None) -> None:
    p = argparse.ArgumentParser(prog="mangaclip",
                                description="Turn a manga PDF into short narrated video clips.")
    p.add_argument("pdf", help="input manga PDF")
    p.add_argument("-o", "--out", default="clips", help="output folder (default: clips)")
    p.add_argument("-n", "--clips", type=int, default=1, help="number of clips to make")
    p.add_argument("-p", "--pages", type=int, default=2, help="pages per clip (default: 2)")
    p.add_argument("--seconds", type=int, default=45, help="target length per clip")
    p.add_argument("--engine", choices=["auto", "claude", "heuristic"], default="auto",
                   help="who picks scenes and writes narration (auto = claude if an API key is set)")
    p.add_argument("--language", default="English", help="narration language")
    p.add_argument("--ltr", action="store_true", help="left-to-right reading (comics/manhwa)")
    p.add_argument("--tts", choices=["edge", "gtts", "pyttsx3", "silent"], default="edge")
    p.add_argument("--voice", help="TTS voice, e.g. en-US-GuyNeural, en-GB-RyanNeural, ja-JP-KeitaNeural")
    p.add_argument("--rate", default="+8%", help="edge-tts speaking rate, e.g. +0%%, +15%%")
    p.add_argument("--format", choices=list(FORMATS), default="vertical")
    p.add_argument("--fps", type=int, default=30)
    p.add_argument("--no-captions", action="store_true")
    p.add_argument("--no-music", action="store_true")
    p.add_argument("--sfx-dir", help="folder of custom SFX files named like impact.wav")
    p.add_argument("--first-page", type=int, help="only consider pages from here")
    p.add_argument("--last-page", type=int, help="only consider pages up to here")
    p.add_argument("--script", help="render from an (edited) script.json instead of analyzing")
    p.add_argument("-v", "--verbose", action="store_true")
    a = p.parse_args(argv)

    logging.basicConfig(level=logging.INFO if a.verbose else logging.WARNING,
                        format="%(levelname)s %(message)s")
    opts = Options(num_clips=a.clips, pages_per_clip=a.pages, clip_seconds=a.seconds,
                   engine=a.engine, language=a.language, right_to_left=not a.ltr, tts=a.tts,
                   voice=a.voice, rate=a.rate, format=a.format, fps=a.fps,
                   captions=not a.no_captions, music=not a.no_music, sfx_dir=a.sfx_dir,
                   first_page=a.first_page, last_page=a.last_page, script_file=a.script)
    outputs = make_clips(a.pdf, a.out, opts, progress=lambda m: print(f"• {m}", flush=True))
    for o in outputs:
        print(o)


if __name__ == "__main__":
    main()
