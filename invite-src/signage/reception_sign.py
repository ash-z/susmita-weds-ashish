"""The reception's welcome sign, hung outside the hall to guide guests: 24 x 36 in, portrait.

    python3 invite-src/signage/reception_sign.py      # -> invite-src/signage/out/reception-sign[-left|-right|-up].{html,png,pdf}
    python3 invite-src/signage/trace_art.py          # only if the toranam / Ganesha art changes

Wording and details come from the invitation (body.html / poster/poster.py). The plaque carries the hall and floor
in large type so it reads from across a lobby; the -left, -right and -up versions add an arrow for wherever it hangs.
Rendering needs node + Playwright's Chromium (render.mjs, next to this file). Fonts are Google Fonts subsets of the
text used, cached in fonts/ (network once); the art is the invitation's own (invite-src/art).
"""
import base64, hashlib, html, pathlib, re, subprocess, urllib.parse, urllib.request

HERE = pathlib.Path(__file__).resolve().parent
ART = HERE.parent / "art"
FONTS = HERE / "fonts"; FONTS.mkdir(exist_ok=True)
OUT = HERE / "out"; OUT.mkdir(exist_ok=True)
W, H = 2400, 3600                          # CSS px: 100 per inch; rendered at 1.5x (150 dpi) and as a print PDF
BLEED = 20                                 # 0.2 in (5 mm) of background past the trim on every side, for the printer
# maroons chosen inside the CMYK gamut (checked against a press profile): the deeper #5a0d1a / #3f0812 the site uses
# print as muddy brown. MAROON is the background's middle, also used for cut-outs in the gold.
MAROON_HI, MAROON, MAROON_LO = "#8a2d36", "#7a2b32", "#6a292e"

T = dict(te="రిసెప్షన్", heading="Reception", bride="Sai Susmita", groom="Ashish",
         when="Sunday · 1 November 2026 · 12:00 PM onwards", hotel="Hotel Tulip Grand", hall="‘Vedha’", floor="5th Floor")
E = lambda s: html.escape(s, quote=False)

# ---------------- fonts: the invitation's pairing ----------------
TEXT = "".join(sorted(set(" ".join(T.values()) + " &·‘’0123456789 ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz")))
def font(family, weight=400):
    key = hashlib.sha1(f"{family}|{weight}|{TEXT}".encode()).hexdigest()[:10]
    f = FONTS / f"{family.replace(' ', '')}-{weight}-{key}.woff2"
    if not f.exists():
        url = f"https://fonts.googleapis.com/css2?family={family.replace(' ', '+')}:wght@{weight}&text={urllib.parse.quote(TEXT)}"
        css = urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 Chrome/120"})).read().decode()
        f.write_bytes(urllib.request.urlopen(re.search(r"src: url\((https://[^)]+)\)", css).group(1)).read())
    return (f"@font-face{{font-family:'{family}';font-weight:{weight};"
            f"src:url(data:font/woff2;base64,{base64.b64encode(f.read_bytes()).decode()}) format('woff2')}}")

def art(name): return "data:image/png;base64," + base64.b64encode((ART / f"{name}.png").read_bytes()).decode()
def outline(name):                         # traced silhouette (trace_art.py) for the gold masks; prints crisp at any size
    return "data:image/svg+xml;base64," + base64.b64encode((HERE / "vector" / f"{name}.svg").read_bytes()).decode()

FOIL = ("linear-gradient(118deg,#7b561a 0%,#c99a3e 14%,#f4dc97 26%,#b3842f 39%,#f8e8b4 52%,#a7772a 64%,"
        "#e2c06c 79%,#8a6220 100%)")
def foil_defs(i):
    return (f'<defs><linearGradient id="{i}" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#7b561a"/>'
            '<stop offset=".15" stop-color="#d4a84a"/><stop offset=".3" stop-color="#f4dc97"/><stop offset=".45" stop-color="#b3842f"/>'
            '<stop offset=".58" stop-color="#f8e8b4"/><stop offset=".72" stop-color="#a7772a"/><stop offset=".86" stop-color="#e2c06c"/>'
            '<stop offset="1" stop-color="#8a6220"/></linearGradient></defs>')

def paisley(x, y, s, rot, fill):
    return (f'<g transform="translate({x},{y}) rotate({rot}) scale({s})" fill="{fill}">'
            '<path d="M0 10 C0 2 8 -3 15 -1 C23 1 27 8 24 14 C21 20 13 22 7 19 C2 16 0 13 0 10 Z M18 2 C22 -4 29 -4 31 0 '
            f'C27 -2 23 -1 21 3 Z"/><circle cx="12" cy="10" r="3" fill="{MAROON}"/></g>')

def frame(w, h, o=70, band=52, step=70):
    """temple-style frame: rules, a band of mango leaves and dots, a row of small arches, rosette corners"""
    c = "url(#ff)"
    i1, i2 = o + band + 20, o + band + 38
    s = [f'<svg width="{w}" height="{h}" style="position:absolute;inset:0">{foil_defs("ff")}']
    for x, sw in ((o, 6), (o + 12, 2), (i1, 4), (i2, 2)):
        s.append(f'<rect x="{x}" y="{x}" width="{w-2*x}" height="{h-2*x}" fill="none" stroke="{c}" stroke-width="{sw}"/>')
    mid = o + 12 + (i1 - o - 12) / 2
    for horizontal in (True, False):
        length = (w if horizontal else h) - 2 * i1 - 120
        n = int(length / step); a0 = ((w if horizontal else h) - n * step) / 2
        for k in range(n + 1):
            p = a0 + k * step
            for side in (0, 1):
                if horizontal:
                    x, y, rot = p, (mid if side == 0 else h - mid), (0 if side == 0 else 180)
                else:
                    x, y, rot = (mid if side == 0 else w - mid), p, (90 if side == 0 else 270)
                s.append(paisley(x - 15, y - 12, 1.25, rot, c) if k % 2 == 0 else f'<circle cx="{x}" cy="{y}" r="7" fill="{c}"/>')
    a = 44; r0 = i2 + 10
    arch = " c0 -18 9 -27 22 -30 c13 3 22 12 22 30"
    for y, flip in ((r0, False), (h - r0, True)):
        n = int((w - 2 * r0) / a); x = (w - n * a) / 2
        d = f"M{x} {y}" + arch * n
        s.append(f'<g transform="{f"translate(0 {2*y}) scale(1 -1)" if flip else ""}"><path d="{d}" fill="none" stroke="{c}" stroke-width="2.4"/></g>')
    for x, flip in ((r0, False), (w - r0, True)):
        n = int((h - 2 * r0) / a); y = (h - n * a) / 2
        d = f"M{y} {x}" + arch * n
        s.append(f'<g transform="translate({x} 0) rotate(90) scale(1 {1 if flip else -1}) translate(0 {-x})"><path d="{d}" fill="none" stroke="{c}" stroke-width="2.4"/></g>')
    for cx, cy in ((mid, mid), (w - mid, mid), (w - mid, h - mid), (mid, h - mid)):
        ring = lambda n, l, wd, off=0: "".join(
            f'<path transform="rotate({k*360/n+off})" d="M0 -9 C-{wd} -{l*.35} -{wd*.7} -{l} 0 -{l} C{wd*.7} -{l} {wd} -{l*.35} 0 -9 Z"/>' for k in range(n))
        s.append(f'<g transform="translate({cx},{cy})" fill="{c}">{ring(12, 46, 10)}<g fill="{MAROON}">{ring(12, 28, 6)}</g>{ring(8, 21, 6, 22.5)}<circle r="9"/></g>')
    s.append("</svg>")
    return "".join(s)

def ornament(y, half=420):
    c = W / 2
    return (f'<svg width="{W}" height="60" style="position:absolute;left:0;top:{y-30}px">{foil_defs("fo")}'
            f'<g stroke="url(#fo)" stroke-width="4" fill="none"><path d="M{c-half} 30 L{c-46} 30"/><path d="M{c+46} 30 L{c+half} 30"/></g>'
            f'<g fill="url(#fo)"><path d="M{c} 8 L{c+22} 30 L{c} 52 L{c-22} 30 Z"/><circle cx="{c-half-14}" cy="30" r="8"/>'
            f'<circle cx="{c+half+14}" cy="30" r="8"/></g></svg>')

def masked(name, x, y, w, h):
    return (f'<div class="foil-img" style="position:absolute;left:{x}px;top:{y}px;width:{w}px;height:{h}px;'
            f'-webkit-mask:url({outline(name)}) center/contain no-repeat;mask:url({outline(name)}) center/contain no-repeat"></div>')

def arrow(direction, color=MAROON):
    """a plain, bold arrow, big enough to read across a lobby"""
    if direction == "up":
        return (f'<svg width="150" height="190" viewBox="-75 -95 150 190">'
                f'<path d="M-20 92 L-20 -10 L-62 -10 L0 -92 L62 -10 L20 -10 L20 92 Z" fill="{color}"/></svg>')
    flip = "scale(-1 1)" if direction == "left" else ""
    return (f'<svg width="420" height="150" viewBox="-210 -75 420 150"><g transform="{flip}">'
            f'<path d="M-200 -20 L110 -20 L110 -62 L200 0 L110 62 L110 20 L-200 20 Z" fill="{color}"/></g></svg>')

def plaque(top, direction=None):
    """the hall and floor on ivory, in a gold-edged cartouche"""
    pw, ph = 1360, (640 if direction is None else 830)
    x0 = (W - pw) / 2
    shape = (f"M{40} 0 L{pw-40} 0 C{pw-40} 30 {pw-10} 40 {pw} 40 L{pw} {ph-40} C{pw-10} {ph-40} {pw-40} {ph-30} {pw-40} {ph} "
             f"L40 {ph} C40 {ph-30} 10 {ph-40} 0 {ph-40} L0 40 C10 40 40 30 40 0 Z")
    svg = (f'<svg width="{pw}" height="{ph}" viewBox="-14 -14 {pw+28} {ph+28}" style="position:absolute;inset:0;overflow:visible">{foil_defs("fp")}'
           f'<path d="{shape}" fill="#fbf4e3" stroke="url(#fp)" stroke-width="14"/>'
           f'<path d="{shape}" transform="translate({pw*.03} {ph*.065}) scale(.94 .87)" fill="none" stroke="#a77b2c" stroke-width="3.5"/></svg>')
    inner = (f'<div style="position:absolute;left:0;right:0;top:70px;text-align:center;font-family:Marcellus;'
             f'font-size:210px;line-height:1.05;color:{MAROON_LO};letter-spacing:4px">{E(T["hall"])}</div>'
             f'<div style="position:absolute;left:0;right:0;top:300px;text-align:center;font-family:Marcellus;'
             f'font-size:150px;line-height:1.1;color:{MAROON};letter-spacing:3px">{E(T["floor"])}</div>')
    if direction:                                         # the arrow, centred under the floor
        inner += f'<div style="position:absolute;left:0;right:0;top:{530 if direction != "up" else 505}px;text-align:center">{arrow(direction)}</div>'
    return f'<div style="position:absolute;left:{x0}px;top:{top}px;width:{pw}px;height:{ph}px">{svg}{inner}</div>'

def sign(direction=None):
    brocade = ('<svg style="position:absolute;inset:0" width="100%" height="100%"><defs><pattern id="br" width="130" height="170" '
               'patternUnits="userSpaceOnUse">' + paisley(24, 40, 1.3, -20, "rgba(0,0,0,.12)") + paisley(89, 125, 1.3, -20, "rgba(0,0,0,.12)") +
               '</pattern></defs><rect width="100%" height="100%" fill="url(#br)"/></svg>')
    grain = ('<svg style="position:absolute;inset:0;mix-blend-mode:multiply;opacity:.08" width="100%" height="100%"><filter id="g">'
             '<feTurbulence type="fractalNoise" baseFrequency=".8" numOctaves="3" seed="7"/><feColorMatrix values="0 0 0 0 .5 0 0 0 0 .45 '
             '0 0 0 0 .4 0 0 0 .9 0"/></filter><rect width="100%" height="100%" filter="url(#g)"/></svg>')
    b = [frame(W, H)]                      # everything from here sits inside the trim
    b.append(masked("toranam", 220, 205, 1960, 693))
    b.append(masked("ganesha", 1050, 470, 300, 390))
    b.append(f'<div class="c foil" style="top:880px;font-family:\'Tiro Telugu\';font-size:120px">{E(T["te"])}</div>')
    b.append(f'<div class="c foil" style="top:1105px;font-family:Marcellus;font-size:200px;letter-spacing:28px;text-indent:28px">{E(T["heading"].upper())}</div>')
    b.append(ornament(1370))
    b.append(f'<div class="c foil" style="top:1400px;font-family:\'Alex Brush\';font-size:330px;line-height:1.1">{E(T["bride"])}</div>')
    b.append(f'<div class="c foil" style="top:1755px;font-family:Marcellus;font-size:120px">&amp;</div>')
    b.append(f'<div class="c foil" style="top:1850px;font-family:\'Alex Brush\';font-size:330px;line-height:1.1">{E(T["groom"])}</div>')
    b.append(f'<div class="c" style="top:2260px;font-family:Marcellus;font-size:74px;letter-spacing:3px;color:#f3e6c8">{E(T["when"])}</div>')
    b.append(ornament(2420, 300))
    b.append(f'<div class="c" style="top:2470px;font-family:Marcellus;font-size:84px;letter-spacing:6px;color:#e9cf86">{E(T["hotel"].upper())}</div>')
    # the peacock pair from Blessings, facing each other across the plaque
    pk = art("peacock")
    b.append(f'<img src="{pk}" style="position:absolute;left:150px;top:2560px;height:880px;transform:scaleX(-1);filter:drop-shadow(0 10px 18px rgba(0,0,0,.45))">')
    b.append(f'<img src="{pk}" style="position:absolute;right:150px;top:2560px;height:880px;filter:drop-shadow(0 10px 18px rgba(0,0,0,.45))">')
    b.append(plaque(2660 if direction is None else 2600, direction))
    css = (font("Alex Brush") + font("Tiro Telugu") + font("Marcellus") + font("Karla", 500) +
           f"*{{margin:0;padding:0;box-sizing:border-box}}html,body{{width:{W+2*BLEED}px;height:{H+2*BLEED}px;overflow:hidden}}"
           f"body{{position:relative;background:radial-gradient(120% 85% at 50% 40%,{MAROON_HI} 0%,{MAROON} 55%,{MAROON_LO} 100%)}}"
           f".c{{position:absolute;left:0;right:0;text-align:center}}"
           f".foil{{background:{FOIL};-webkit-background-clip:text;background-clip:text;color:transparent;"
           f"filter:drop-shadow(0 3px 0 rgba(0,0,0,.45)) drop-shadow(0 -1px 0 rgba(255,236,190,.25))}}"
           f".foil-img{{background:{FOIL};filter:drop-shadow(0 4px 0 rgba(0,0,0,.45))}}"
           f"@page{{size:{(W+2*BLEED)/100}in {(H+2*BLEED)/100}in;margin:0}}")
    return (f'<!doctype html><html><head><meta charset="utf-8"><style>{css}</style></head><body>{brocade}{grain}'
            f'<div id="trim" style="position:absolute;left:{BLEED}px;top:{BLEED}px;width:{W}px;height:{H}px">{"".join(b)}</div></body></html>')

names = []
for d in (None, "left", "right", "up"):
    n = "reception-sign" + (f"-{d}" if d else "")
    (OUT / f"{n}.html").write_text(sign(d)); names.append(n)
subprocess.run(["node", str(HERE / "render.mjs"), str(OUT), *names], check=True)
