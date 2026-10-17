"""End-to-end: PDF -> page scan -> best segments -> scripts -> narrated video clips."""

from __future__ import annotations

import json
import logging
import os
from dataclasses import asdict, dataclass
from typing import Callable

from .analyze import ClaudeAnalyzer, HeuristicAnalyzer, pick_segments
from .pdf import load_pages
from .render import Renderer
from .script import ClipScript
from .tts import TTS

log = logging.getLogger(__name__)


@dataclass
class Options:
    num_clips: int = 1
    pages_per_clip: int = 2
    clip_seconds: int = 45
    engine: str = "auto"  # auto | claude | heuristic
    language: str = "English"
    right_to_left: bool = True
    tts: str = "edge"
    voice: str | None = None
    rate: str = "+8%"
    format: str = "vertical"
    fps: int = 30
    captions: bool = True
    music: bool = True
    sfx_dir: str | None = None
    first_page: int | None = None
    last_page: int | None = None
    script_file: str | None = None  # re-render an edited script.json instead of analyzing


def make_clips(pdf_path: str, out_dir: str, opts: Options,
               progress: Callable[[str], None] = lambda msg: None) -> list[str]:
    os.makedirs(out_dir, exist_ok=True)
    progress("Rendering PDF pages")
    pages = load_pages(pdf_path, first=opts.first_page, last=opts.last_page)
    if not pages:
        raise ValueError("The PDF has no pages in the selected range")
    by_num = {p.number: p for p in pages}

    if opts.script_file:
        with open(opts.script_file, encoding="utf-8") as f:
            data = json.load(f)
        scripts = [ClipScript.from_dict(d) for d in (data if isinstance(data, list) else [data])]
    else:
        engine = opts.engine
        if engine == "auto":
            engine = "claude" if (os.environ.get("ANTHROPIC_API_KEY")
                                  or os.environ.get("ANTHROPIC_AUTH_TOKEN")) else "heuristic"
        progress(f"Analyzing {len(pages)} pages ({engine})")
        title = os.path.splitext(os.path.basename(pdf_path))[0].replace("_", " ")
        analyzer = (ClaudeAnalyzer(opts.language, opts.right_to_left) if engine == "claude"
                    else HeuristicAnalyzer(opts.right_to_left, title=title))
        infos = analyzer.scan(pages)
        with open(os.path.join(out_dir, "pages.json"), "w", encoding="utf-8") as f:
            json.dump([asdict(i) for i in infos], f, indent=2, ensure_ascii=False)
        segments = pick_segments(infos, min(opts.pages_per_clip, len(pages)), opts.num_clips)
        scripts = []
        for seg in segments:
            progress(f"Writing narration for pages {seg[0]}-{seg[-1]}")
            scripts.append(analyzer.write_script([by_num[n] for n in seg], infos,
                                                 opts.clip_seconds))
        with open(os.path.join(out_dir, "script.json"), "w", encoding="utf-8") as f:
            f.write("[\n" + ",\n".join(s.to_json() for s in scripts) + "\n]\n")

    tts = TTS(opts.tts, opts.voice, opts.rate, cache_dir=os.path.join(out_dir, ".tts-cache"))
    renderer = Renderer(opts.format, opts.fps, opts.captions, tts, opts.sfx_dir, opts.music)
    outputs = []
    for i, script in enumerate(scripts, 1):
        missing = [p for p in script.pages if p not in by_num]
        if missing:
            raise ValueError(f"Script refers to pages not loaded from the PDF: {missing}")
        progress(f"Rendering clip {i}/{len(scripts)}: {script.title}")
        out = os.path.join(out_dir, f"clip_{i:02d}_p{script.pages[0]}-{script.pages[-1]}.mp4")
        renderer.render(script, by_num, out)
        outputs.append(out)
    progress("Done")
    return outputs
