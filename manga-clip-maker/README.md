# Manga Clip Maker

Turn a manga PDF into short narrated video clips of its most interesting pages, with
voice-over, sound effects, background music and captions. It's built for Shorts, Reels and TikTok.

```
manga.pdf ─► render pages ─► Claude reads every page & scores it ─► pick best page runs
          ─► Claude writes a panel-by-panel narration script (+ SFX cues, mood)
          ─► TTS voice-over ─► camera pans/zooms across panels ─► SFX + music mix ─► clip.mp4
```

## Quick start

```bash
cd manga-clip-maker
pip install -r requirements.txt          # also needs ffmpeg on PATH
export ANTHROPIC_API_KEY=sk-ant-...      # for scene picking + narration

python -m mangaclip my_manga.pdf -o clips -n 3 -p 2
```

This writes `clips/clip_01_p12-13.mp4` and the other clips, plus:

- `pages.json`: Claude's one-line summary and a 0-10 "clip-worthiness" score for every page
- `script.json`: the full script (panels, narration, SFX, mood). You can edit it and re-render
  without calling the API again:

```bash
python -m mangaclip my_manga.pdf -o clips --script clips/script.json
```

### Web app

```bash
python -m mangaclip.web.app      # http://localhost:5000
```

Upload a PDF, choose your options, then watch and download the clips in the browser.

## Options

| Flag | Default | Meaning |
|---|---|---|
| `-n/--clips` | 1 | number of clips |
| `-p/--pages` | 2 | consecutive pages per clip |
| `--seconds` | 45 | target clip length (guides the narration length) |
| `--format` | vertical | `vertical` 1080×1920, `landscape` 1920×1080, `square` |
| `--language` | English | narration language (Claude translates Japanese pages, for example) |
| `--style` | recap | narrator: `recap`, `dramatic`, `funny`, `hype`, or your own description in quotes |
| `--ltr` | off | left-to-right panel order (western comics, manhwa) |
| `--tts` | auto | `auto` (edge → piper → gtts → pyttsx3), or one of `edge`, `piper`, `gtts`, `pyttsx3`, `silent` |
| `--voice` | en-US-AndrewMultilingualNeural | edge voice (`edge-tts --list-voices`), Piper voice (`en_US-ryan-high`), or a `.onnx` path |
| `--rate` | +5% | base speaking rate |
| `--engine` | auto | `claude`, or `heuristic` for offline mode with no API key |
| `--sfx-dir` | | folder of your own SFX files, e.g. `impact.wav` or `whoosh.mp3` |
| `--first-page/--last-page` | | limit which pages are considered |
| `--no-captions`, `--no-music` | | |

## Narration

The narration is the core of each clip, so it gets the most care:

- **It's written as one story.** Claude keeps a cast list while scanning, so characters are
  named and introduced consistently. Each clip is narrated for someone who hasn't read the manga:
  who people are, what is at stake, and the key dialogue retold in the narrator's own words.
- **Its length fits the clip.** `--seconds` becomes a spoken-word budget (about 2.5 words per
  second). Each panel stays on screen until its line is finished, so a line is never cut off.
- **Lines are written for the ear.** The prompt asks for short sentences and no symbols, emojis
  or parentheses, and the text is cleaned again before it reaches the voice.
- **Each line has a tone.** `neutral`, `tense`, `excited`, `whisper`, `sad` or `comedic` changes
  the voice's rate, pitch and volume.
- **It's never silently missing.** If a voice engine fails (no internet, for example), the next
  one is used and a warning is printed. If none work, the run stops with an error rather than
  producing a mute clip. The run ends with a line like
  `Narration: 12 lines in 2 clip(s), voice engine: edge`.

Voice engines, best first: **edge** (free Microsoft neural voices, needs internet), **piper**
(offline neural voices; the voice downloads once to `~/.cache/mangaclip/piper`), **gtts**, and
**pyttsx3** (robotic, offline; needs espeak on Linux).

To polish a clip, edit the narration lines in `script.json` and re-render with `--script`.

## How it works

- **`pdf.py`**: renders pages with PyMuPDF.
- **`analyze.py`** has two stages:
  1. *Scan*: pages go to Claude (`claude-opus-5-5`) in batches of 16. Claude summarizes each page,
     scores how good it would be in a clip, and flags non-story pages such as covers and credits.
     A running "story so far" is passed along so later batches have context.
  2. *Script*: the best run of consecutive pages is picked, then Claude sees those pages at
     higher resolution. It returns the panels in reading order (bounding boxes), the narration for
     each panel, an SFX cue, emphasis flags and the mood. Both stages use structured JSON output.
- **`panels.py`**: XY-cut panel detection along white gutters. Claude's boxes are snapped to
  detected panels for tight framing. In heuristic mode, the detected panels are used directly.
- **`sfx.py`**: every sound effect (whoosh, impact, punch, slash, explosion, heartbeat, sting,
  chime, boing, rumble, gasp) and the mood music beds are synthesized with numpy, so there are no
  assets to license.
- **`render.py`**: builds the timeline (title card, a pan to each panel, a hold while the
  narration plays, punch-in zoom and shake on big moments, fades between pages, outro card). It
  renders frames with Pillow and pipes them into ffmpeg. Music ducks under the voice.

## Notes

- **Offline mode** (`--engine heuristic`) picks visually intense pages (speed lines, splash
  pages) and pans across them with SFX. It can't read the story, so its narration is minimal.
- Only use manga you have the rights to share.
