"""The reception's welcome sign, hung outside the hall to guide guests: 24 x 36 in, portrait.

    python3 invite-src/signage/reception_sign.py      # -> invite-src/signage/out/reception-sign.{html,png,pdf}
    python3 invite-src/signage/trace_art.py          # only if the toranam / Ganesha art changes

Wording and details come from the invitation (body.html / poster/poster.py). The plaque carries the hall and floor
in large type so it reads from across a lobby. The reception is by day and the board stands outdoors, so it is ivory
with maroon type and deep gold ornament: light ink on dark only where it must read first (the plaque).
Rendering needs node + Playwright's Chromium (render.mjs, next to this file). Fonts are Google Fonts subsets of the
text used, cached in fonts/ (network once); the art is the invitation's own (invite-src/art).
"""
import base64, hashlib, html, pathlib, re, subprocess, urllib.parse, urllib.request

HERE = pathlib.Path(__file__).resolve().parent
ART = HERE.parent / "art"
PHOTOS = HERE.parent / "photos"
FONTS = HERE / "fonts"; FONTS.mkdir(exist_ok=True)
OUT = HERE / "out"; OUT.mkdir(exist_ok=True)
W, H = 2400, 3600                          # CSS px: 100 per inch; rendered at 1.5x (150 dpi) and as a print PDF
BLEED = 20                                 # 0.2 in (5 mm) of background past the trim on every side, for the printer
# colours chosen inside the CMYK gamut (checked against a press profile): the deeper #5a0d1a / #3f0812 the site uses
# print as muddy brown
MAROON, MAROON_LO = "#7a2b32", "#5e2429"
IVORY, IVORY_LO = "#fbf4e3", "#f1e2bf"     # the board, centre to edge
GOLD = "#8a5d17"                           # solid deep gold for small type: a light foil would wash out in sunlight

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

# deep gold foil for ivory: its highlights stop well short of the board's colour so the shapes hold in daylight
FOIL = ("linear-gradient(118deg,#6e4a12 0%,#a8781f 14%,#c99a3e 26%,#8f6418 39%,#c4952f 52%,#83591a 64%,"
        "#b0822a 79%,#6a4612 100%)")
def foil_defs(i):
    return (f'<defs><linearGradient id="{i}" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#6e4a12"/>'
            '<stop offset=".15" stop-color="#a8781f"/><stop offset=".3" stop-color="#c99a3e"/><stop offset=".45" stop-color="#8f6418"/>'
            '<stop offset=".58" stop-color="#c4952f"/><stop offset=".72" stop-color="#83591a"/><stop offset=".86" stop-color="#b0822a"/>'
            '<stop offset="1" stop-color="#6a4612"/></linearGradient></defs>')

def paisley(x, y, s, rot, fill, hole=IVORY):
    return (f'<g transform="translate({x},{y}) rotate({rot}) scale({s})" fill="{fill}">'
            '<path d="M0 10 C0 2 8 -3 15 -1 C23 1 27 8 24 14 C21 20 13 22 7 19 C2 16 0 13 0 10 Z M18 2 C22 -4 29 -4 31 0 '
            f'C27 -2 23 -1 21 3 Z"/><circle cx="12" cy="10" r="3" fill="{hole}"/></g>')

def frame(w, h, o=70, band=52, step=70):
    """temple-style frame in maroon: rules, a band of mango leaves and dots, a row of small arches, rosette corners"""
    c = MAROON
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
        s.append(f'<g transform="translate({cx},{cy})" fill="{c}">{ring(12, 46, 10)}<g fill="{IVORY}">{ring(12, 28, 6)}</g>{ring(8, 21, 6, 22.5)}<circle r="9"/></g>')
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

def photo(top, w=880, h=1100, rim=14, mat=8):
    """the engagement portrait (the site's cover crop) in the site's temple-arch window: gold rim, maroon mat"""
    src, (cx, cy, cw) = PHOTOS / "Screenshot_2026-09-23-07-59-16-387_com.google.android.apps.nbu.files.jpg", (140, 100, 960)
    iw = w - 2 * (rim + mat); k = iw / cw                 # show the 960-wide crop across the window
    uri = "data:image/jpeg;base64," + base64.b64encode(src.read_bytes()).decode()
    arch = lambda r: f"border-radius:{r}px {r}px 24px 24px"
    return (f'<div class="foil-img" style="position:absolute;left:{(W-w)/2}px;top:{top}px;width:{w}px;height:{h}px;padding:{rim}px;{arch(w)};'
            f'filter:drop-shadow(0 12px 20px rgba(90,45,10,.3))"><div style="width:100%;height:100%;padding:{mat}px;background:{MAROON};{arch(w)}">'
            f'<div style="position:relative;width:100%;height:100%;overflow:hidden;{arch(w)}"><img src="{uri}" style="position:absolute;'
            f'width:{1200*k}px;left:{-cx*k}px;top:{-cy*k}px"></div></div></div>')

def plaque(top):
    """the hall and floor, light on maroon in a gold-edged cartouche: the one thing that must read from afar"""
    pw, ph = 1560, 440
    x0 = (W - pw) / 2
    shape = (f"M{40} 0 L{pw-40} 0 C{pw-40} 30 {pw-10} 40 {pw} 40 L{pw} {ph-40} C{pw-10} {ph-40} {pw-40} {ph-30} {pw-40} {ph} "
             f"L40 {ph} C40 {ph-30} 10 {ph-40} 0 {ph-40} L0 40 C10 40 40 30 40 0 Z")
    svg = (f'<svg width="{pw}" height="{ph}" viewBox="-14 -14 {pw+28} {ph+28}" style="position:absolute;inset:0;overflow:visible">{foil_defs("fp")}'
           f'<path d="{shape}" fill="{MAROON}" stroke="url(#fp)" stroke-width="14"/>'
           f'<path d="{shape}" transform="translate({pw*.03} {ph*.065}) scale(.94 .87)" fill="none" stroke="#d9b45e" stroke-width="3.5"/></svg>')
    inner = (f'<div style="position:absolute;left:0;right:0;top:40px;text-align:center;font-family:Marcellus;'
             f'font-size:180px;line-height:1.05;color:{IVORY};letter-spacing:4px">{E(T["hall"])}</div>'
             f'<div style="position:absolute;left:0;right:0;top:238px;text-align:center;font-family:Marcellus;'
             f'font-size:124px;line-height:1.1;color:#efd48c;letter-spacing:3px">{E(T["floor"])}</div>')
    return f'<div style="position:absolute;left:{x0}px;top:{top}px;width:{pw}px;height:{ph}px">{svg}{inner}</div>'

def sign():
    brocade = ('<svg style="position:absolute;inset:0" width="100%" height="100%"><defs><pattern id="br" width="130" height="170" '
               'patternUnits="userSpaceOnUse">' + paisley(24, 40, 1.3, -20, "rgba(150,100,30,.10)", "none") + paisley(89, 125, 1.3, -20, "rgba(150,100,30,.10)", "none") +
               '</pattern></defs><rect width="100%" height="100%" fill="url(#br)"/></svg>')
    # (no paper grain: it barely shows in print and turns the PDF into a 150 MB full-page bitmap)
    b = [frame(W, H)]                      # everything from here sits inside the trim
    b.append(masked("toranam", 220, 205, 1960, 693))
    b.append(masked("ganesha", 1050, 470, 300, 390))
    b.append(f'<div class="c foil" style="top:852px;font-family:\'Tiro Telugu\';font-size:104px">{E(T["te"])}</div>')
    b.append(f'<div class="c" style="top:1012px;font-family:Marcellus;font-size:165px;letter-spacing:24px;text-indent:24px;color:{MAROON}">{E(T["heading"].upper())}</div>')
    # the engagement portrait
    b.append(photo(1225, w=990, h=1225))
    b.append(f'<div class="c" style="top:2462px;font-family:\'Alex Brush\';font-size:230px;line-height:1.1;color:{MAROON}">{E(T["bride"])}'
             f'<span style="font-family:Marcellus;font-size:100px;margin:0 50px;vertical-align:middle;color:{GOLD}">&amp;</span>{E(T["groom"])}</div>')
    b.append(f'<div class="c" style="top:2742px;font-family:Marcellus;font-size:64px;letter-spacing:3px;color:{MAROON_LO}">{E(T["when"])}</div>')
    b.append(f'<div class="c" style="top:2836px;font-family:Marcellus;font-size:72px;letter-spacing:6px;color:{GOLD}">{E(T["hotel"].upper())}</div>')
    b.append(plaque(2968))
    css = (font("Alex Brush") + font("Tiro Telugu") + font("Marcellus") + font("Karla", 500) +
           f"*{{margin:0;padding:0;box-sizing:border-box}}html,body{{width:{W+2*BLEED}px;height:{H+2*BLEED}px;overflow:hidden}}"
           f"body{{position:relative;background:radial-gradient(120% 85% at 50% 40%,{IVORY} 0%,{IVORY} 45%,{IVORY_LO} 100%)}}"
           f".c{{position:absolute;left:0;right:0;text-align:center}}"
           f".foil{{background:{FOIL};-webkit-background-clip:text;background-clip:text;color:transparent;"
           f"filter:drop-shadow(0 2px 0 rgba(90,50,10,.18))}}"
           f".foil-img{{background:{FOIL};filter:drop-shadow(0 2px 0 rgba(90,50,10,.18))}}"
           f"@page{{size:{(W+2*BLEED)/100}in {(H+2*BLEED)/100}in;margin:0}}")
    return (f'<!doctype html><html><head><meta charset="utf-8"><style>{css}</style></head><body>{brocade}'
            f'<div id="trim" style="position:absolute;left:{BLEED}px;top:{BLEED}px;width:{W}px;height:{H}px">{"".join(b)}</div></body></html>')

(OUT / "reception-sign.html").write_text(sign())
subprocess.run(["node", str(HERE / "render.mjs"), str(OUT), "reception-sign"], check=True)
