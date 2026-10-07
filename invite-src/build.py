"""Assemble the invitation into one self-contained page.

    cd invite-src && npm install && python3 build.py

Builds three invitations from the same files: the relatives' one, the
friends' one (which adds the day-before page) and the groom's side's one
(/bhimanpalliwar/: the relatives' one with the groom named first throughout). For each it writes the page
GitHub Pages serves (docs/index.html, docs/friends/index.html), the same page
without <head> for a Claude artifact (build/artifact[-friends].html), and that
with a DEV badge for the dev preview (build/artifact-dev[-friends].html).
three.js is tree-shaken by esbuild and inlined, so the page makes no
runtime request except the Google Fonts stylesheet.
"""
import pathlib, subprocess

here = pathlib.Path(__file__).resolve().parent
root = here.parent
build = here / "build"
build.mkdir(exist_ok=True)

subprocess.run(["npx", "esbuild", "three-entry.js", "--bundle", "--minify", "--format=iife",
                "--global-name=THREE", "--outfile=build/three.min.js", "--legal-comments=none"],
               cwd=here, check=True)

import base64, re

def inline_art(text):
    """Replace {{art:name}} with the art/name.webp file as a data URI."""
    def sub(m):
        data = (here / "art" / f"{m.group(1)}.webp").read_bytes()
        return "data:image/webp;base64," + base64.b64encode(data).decode()
    return re.sub(r"\{\{art:([a-z0-9-]+)\}\}", sub, text)

style = inline_art((here / "style.html").read_text())
src   = inline_art((here / "body.html").read_text())
app   = (here / "app.js").read_text()
three = (build / "three.min.js").read_text()

# two invitations from one source: <!--friends-->...<!--/friends--> blocks in
# body.html (the day-before page and its tab) appear only in the friends' one
FRIENDS = re.compile(r"<!--friends-->\n(.*?)<!--/friends-->\n", re.S)
bodies = {"relatives": FRIENDS.sub("", src), "friends": FRIENDS.sub(r"\1", src)}

# the groom's side (/bhimanpalliwar/): the relatives' invitation, groom first throughout
# (names, photo order, captions, calendar titles, and the groom's parents before the bride's)
def groom_first(body):
    def swap(text, old, new, count=1):
        assert text.count(old) == count, ("groom variant: expected", count, old)
        return text.replace(old, new)
    body = swap(body, '<span class="n">Sai Susmita</span><span class="amp">&amp;</span><span class="n">Ashish</span>',
                      '<span class="n">Ashish</span><span class="amp">&amp;</span><span class="n">Sai Susmita</span>')   # the envelope
    body = re.sub(r'(<span class="nm">)Sai Susmita(</span>\s*<span class="weds">weds</span>\s*<span class="nm">)Ashish(</span>)',
                  r'\1Ashish\2Sai Susmita\3', body)
    # photos: his card before hers
    her = re.search(r'\n\s*<figure class="card" data-mood="her".*?</figure>', body, re.S)
    him = re.search(r'\n\s*<figure class="card" data-mood="him".*?</figure>', body, re.S)
    assert her and him and her.end() <= him.start(), "groom variant: photo cards not found in order"
    body = body[:her.start()] + him.group(0) + body[her.end():him.start()] + her.group(0) + body[him.end():]
    body = body.replace('aria-label="Susmita and Ashish"', 'aria-label="Ashish and Susmita"')
    body = swap(body, '<span class="cap-name">Susmita &amp; Ashish</span>', '<span class="cap-name">Ashish &amp; Susmita</span>')
    body = swap(body, 'text=Susmita%20weds%20Ashish', 'text=Ashish%20weds%20Susmita')
    body = body.replace('text=Susmita%20%26%20Ashish', 'text=Ashish%20%26%20Susmita')
    # Blessings: the groom's parents first
    fams = re.search(r'(<div class="fams reveal">\s*)(<div class="fam">.*?</div>)(\s*)(<div class="fam">.*?</div>)', body, re.S)
    assert fams and 'the bride' in fams.group(2) and 'the groom' in fams.group(4), "groom variant: families not found"
    body = body[:fams.start()] + fams.group(1) + fams.group(4) + fams.group(3) + fams.group(2) + body[fams.end():]
    body = swap(body, '<p class="sig-en">Sai Susmita &amp; Ashish</p>', '<p class="sig-en">Ashish &amp; Sai Susmita</p>')
    assert 'Sai Susmita</span>\n' not in body.split('<h1 class="names">')[1][:120], "groom variant: hero names not swapped"
    return body
bodies["groom"] = groom_first(bodies["relatives"])
PATH = {"relatives": "", "friends": "friends/", "groom": "bhimanpalliwar/"}
TITLE = {"groom": "Ashish weds Sai Susmita"}       # page title and link preview; the others use `name`
SONG = {"groom": "relatives"}                      # the groom's side plays the relatives' song

def tail(invite):
    body = bodies[invite]
    used = sorted(set(re.findall(r'data-art="([a-z0-9-]+)"', body)))
    art  = "var ART={" + ",".join(
        f'"{n}":"data:image/webp;base64,' + base64.b64encode((here / "art" / f"{n}.webp").read_bytes()).decode() + '"'
        for n in used) + "};"
    if invite != "relatives":
        art += f'var INVITE="{invite}";'
    return "\n<script>" + art + "</script>\n<script>" + three + "</script>\n<script>" + app + "</script>\n"

url  = "https://susmitawedsashish.in/"
name = "Sai Susmita weds Ashish"
desc = "Thursday, 29 October 2026 · Visakhapatnam. We ask for your presence, and for your blessings."
favicon = ("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 64'%3E"
           "%3Ccircle cx='32' cy='32' r='30' fill='%23F7F2E8'/%3E%3Ccircle cx='32' cy='32' r='21' fill='none' "
           "stroke='%23A97C2B' stroke-width='2.5'/%3E%3Ccircle cx='32' cy='32' r='6' fill='%239A3A32'/%3E%3C/svg%3E")
def head(page_url, title=None):
    title = title or name
    return f"""<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<meta name="description" content="{desc}">
<meta name="theme-color" content="#F7F2E8">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
<meta property="og:type" content="website">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{desc}">
<meta property="og:url" content="{page_url}">
<meta property="og:image" content="{url}og.jpg">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image">
<link rel="icon" href="{favicon}">
"""

# photographs: separate files next to the page on GitHub Pages (loaded as the deck
# needs them); embedded in the artifact, which has to be one file
photos = here / "photos" / "out"
(root / "docs" / "photos").mkdir(exist_ok=True)
for f in photos.glob("*.webp"):
    (root / "docs" / "photos" / f.name).write_bytes(f.read_bytes())
def photo_src(inline, up=""):
    def sub(m):
        n = m.group(1)
        if inline:
            return 'src="data:image/webp;base64,' + base64.b64encode((photos / f"{n}.webp").read_bytes()).decode() + '"'
        return f'src="{up}photos/{n}.webp"'
    return sub
badge = ('<div aria-hidden="true" style="position:fixed;top:calc(env(safe-area-inset-top,0px) + 8px);left:8px;'
         'z-index:9999;pointer-events:none;padding:2px 8px;border-radius:999px;background:#9A3A32;color:#fff;'
         'font:600 10px/16px Karla,system-ui,sans-serif;letter-spacing:.12em">DEV</div>')
# each invitation has its own song: docs/music/relatives.mp3 and docs/music/friends.mp3 (or .m4a / .wav).
# The pages point at the folder, so a song dropped in works without a rebuild; the artifacts have to be one
# file, so they embed it (if there is one)
music_dir = root / "docs" / "music"
def song_for(invite):
    invite = SONG.get(invite, invite)
    return next((music_dir / f"{invite}.{e}" for e in ("mp3", "m4a", "wav") if (music_dir / f"{invite}.{e}").exists()), None)
AUDIO = re.compile(r'<audio id="song"[^>]*>.*?</audio>', re.S)
def music_src(up, invite):
    invite = SONG.get(invite, invite)
    return lambda m: f'src="{up}music/{invite}.{m.group(1)}"'
def music_inline(body, invite):
    song = song_for(invite)
    if not song:
        return AUDIO.sub('<audio id="song" loop preload="none"></audio>', body)
    kind = {"mp3": "audio/mpeg", "m4a": "audio/mp4", "wav": "audio/wav"}[song.suffix[1:]]
    data = base64.b64encode(song.read_bytes()).decode()
    return AUDIO.sub(f'<audio id="song" loop preload="none"><source src="data:{kind};base64,{data}" type="{kind}"></audio>', body)

for invite, sub in PATH.items():
    title = TITLE.get(invite, name)
    styled = style.replace(f"<title>{name}</title>", f"<title>{title}</title>")
    body, suffix = bodies[invite], "" if invite == "relatives" else "-" + invite
    up = "../" * sub.count("/")
    page = re.sub(r'data-photo="([a-z0-9-]+)"', photo_src(False, up), body)
    page = re.sub(r'data-music="([a-z0-9]+)"', music_src(up, invite), page)
    one  = music_inline(re.sub(r'data-photo="([a-z0-9-]+)"', photo_src(True), body), invite)
    (build / f"artifact{suffix}.html").write_text(styled + "\n" + one + tail(invite))
    # the dev previews: same pages, marked so they are never mistaken for the ones guests see
    (build / f"artifact-dev{suffix}.html").write_text(
        style.replace(f"<title>{name}</title>", f"<title>{title} (dev{', ' + invite if suffix else ''})</title>")
        + "\n" + badge + "\n" + one + tail(invite))
    (root / "docs" / sub).mkdir(exist_ok=True)
    (root / "docs" / sub / "index.html").write_text(
        '<!doctype html>\n<html lang="en" data-theme="light">\n<head>\n' + head(url + sub, title) + styled +
        "\n</head>\n<body>\n" + page + tail(invite) + "</body>\n</html>\n")
# the address is /bhimanpalliwar/ (all lowercase, the couple's choice); GitHub Pages is case-sensitive,
# so the capitalised spelling forwards there
(root / "docs" / "Bhimanpalliwar").mkdir(exist_ok=True)
(root / "docs" / "Bhimanpalliwar" / "index.html").write_text(
    '<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n<title>Ashish weds Sai Susmita</title>\n'
    f'<link rel="canonical" href="{url}bhimanpalliwar/">\n<meta http-equiv="refresh" content="0;url=../bhimanpalliwar/">\n'
    '<script>location.replace("../bhimanpalliwar/" + location.hash)</script>\n</head>\n<body></body>\n</html>\n')
print("wrote docs/index.html, docs/friends/index.html, docs/bhimanpalliwar/index.html and build/artifact{,-dev}{,-friends,-groom}.html")
