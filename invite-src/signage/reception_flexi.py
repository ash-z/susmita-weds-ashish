"""The reception board as a typical Indian wedding flexi, made minimal: 24 x 36 in (2 x 3 ft), portrait.

    python3 invite-src/signage/reception_flexi.py     # -> invite-src/signage/out/reception-flexi.{html,png,pdf}

Everything a reception flexi has (Ganesha, a toranam, the couple's photograph large, the names, the date and the
hall) and little else: an ivory board, three colours (maroon, gold, a touch of marigold), the toranam reduced to a
gold string of outlined mango leaves and marigold dots, and the photograph in a tall temple arch drawn as a single
gold line. Same wording as the other boards (groom first, at the couple's request).
"""
import base64, html, subprocess
import common
from common import W, H, BLEED, OUT, HERE

PHOTOS = HERE.parent / "photos"
T = dict(te="రిసెప్షన్", heading="Reception", bride="Sai Susmita", groom="Ashish",
         when="Sunday · 1 November 2026 · 12:00 PM onwards", hall="‘Vedha’ · 5th Floor", hotel="Hotel Tulip Grand")
E = lambda s: html.escape(s, quote=False)
TEXT = "".join(sorted(set(" ".join(T.values()) + " &·‘’0123456789 ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz")))
def font(family, weight=400): return common.font(family, weight, TEXT)

# inside the CMYK gamut, and dark enough on ivory to read outdoors by day
IVORY, MAROON, GOLD, MARIGOLD = "#fbf6ee", "#7a2b32", "#a87f3a", "#e48c1c"

def toranam(y=150, x0=170, x1=W - 170, step=76):
    """the toranam as a line: a gold string, outlined mango leaves hanging from it, a marigold between every few"""
    n = int((x1 - x0) / step); x0 = (W - n * step) / 2
    s = [f'<path d="M{x0 - 30} {y} L{x0 + n * step + 30} {y}" stroke="{GOLD}" stroke-width="5"/>']
    for k in range(n + 1):
        x = x0 + k * step
        if k % 4 == 2:
            s.append(f'<path d="M{x} {y} L{x} {y + 38}" stroke="{GOLD}" stroke-width="3"/>'
                     f'<circle cx="{x}" cy="{y + 62}" r="24" fill="{MARIGOLD}"/><circle cx="{x}" cy="{y + 62}" r="9" fill="#f6b84b"/>')
        else:
            long = 132 if k % 2 else 106              # alternate lengths, as a strung toranam hangs
            s.append(f'<path d="M{x} {y} C{x + 24} {y + long * .35} {x + 16} {y + long * .8} {x} {y + long} '
                     f'C{x - 16} {y + long * .8} {x - 24} {y + long * .35} {x} {y} Z" fill="none" stroke="{GOLD}" stroke-width="4.5"/>'
                     f'<path d="M{x} {y + 8} L{x} {y + long - 12}" stroke="{GOLD}" stroke-width="2"/>')
    for x in (x0 - 30, x0 + n * step + 30):           # a bell at each end
        s.append(f'<path d="M{x} {y} L{x} {y + 60}" stroke="{GOLD}" stroke-width="3"/>'
                 f'<path d="M{x - 22} {y + 108} C{x - 22} {y + 70} {x + 22} {y + 70} {x + 22} {y + 108} Z" fill="{GOLD}"/>'
                 f'<circle cx="{x}" cy="{y + 116}" r="7" fill="{GOLD}"/>')
    return f'<svg width="{W}" height="{y + 200}" style="position:absolute;left:0;top:0">{"".join(s)}</svg>'

def ganesha(x, y, w, h):
    uri = "data:image/svg+xml;base64," + base64.b64encode((HERE / "vector" / "ganesha.svg").read_bytes()).decode()
    return (f'<div style="position:absolute;left:{x}px;top:{y}px;width:{w}px;height:{h}px;background:{GOLD};'
            f'-webkit-mask:url({uri}) center/contain no-repeat;mask:url({uri}) center/contain no-repeat"></div>')

def photo(top, w, h, gap=26):
    """the engagement portrait in a tall temple arch; a single gold line follows the arch a little outside it"""
    src, (cx, cy, cw) = PHOTOS / "Screenshot_2026-09-23-07-59-16-387_com.google.android.apps.nbu.files.jpg", (170, 60, 980)
    k = w / cw
    uri = "data:image/jpeg;base64," + base64.b64encode(src.read_bytes()).decode()
    x = (W - w) / 2
    return (f'<div style="position:absolute;left:{x - gap}px;top:{top - gap}px;width:{w + 2 * gap}px;height:{h + 2 * gap}px;'
            f'border:5px solid {GOLD};border-radius:{w}px {w}px 0 0"></div>'
            f'<div style="position:absolute;left:{x}px;top:{top}px;width:{w}px;height:{h}px;overflow:hidden;border-radius:{w}px {w}px 0 0">'
            f'<img src="{uri}" style="position:absolute;width:{1200 * k}px;left:{-cx * k}px;top:{-cy * k}px"></div>')

def rule(y, half=380):
    c = W / 2
    return (f'<svg width="{W}" height="40" style="position:absolute;left:0;top:{y - 20}px"><path d="M{c - half} 20 L{c - 30} 20 M{c + 30} 20 L{c + half} 20" '
            f'stroke="{GOLD}" stroke-width="3"/><path d="M{c} 8 L{c + 12} 20 L{c} 32 L{c - 12} 20 Z" fill="{MARIGOLD}"/></svg>')

def board():
    b = [toranam(), ganesha(1140, 330, 120, 156)]
    b.append(f'<div class="c" style="top:500px;font-family:\'Tiro Telugu\';font-size:66px;color:{GOLD}">{E(T["te"])}</div>')
    b.append(f'<div class="c" style="top:598px;font-family:Marcellus;font-size:84px;letter-spacing:34px;text-indent:34px;color:{MAROON}">{E(T["heading"].upper())}</div>')
    b.append(photo(810, 1360, 1700))
    b.append(f'<div class="c" style="top:2562px;font-family:\'Alex Brush\';font-size:230px;line-height:1.1;color:{MAROON}">{E(T["groom"])}'
             f'<span style="font-family:Marcellus;font-size:96px;margin:0 50px;vertical-align:middle;color:{GOLD}">&amp;</span>{E(T["bride"])}</div>')
    b.append(rule(2878))
    b.append(f'<div class="c" style="top:2928px;font-family:Marcellus;font-size:64px;letter-spacing:3px;color:#4b3530">{E(T["when"])}</div>')
    b.append(f'<div class="c" style="top:3058px;font-family:Marcellus;font-size:132px;letter-spacing:4px;color:{MAROON}">{E(T["hall"])}</div>')
    b.append(f'<div class="c" style="top:3250px;font-family:Marcellus;font-size:62px;letter-spacing:16px;text-indent:16px;color:{GOLD}">{E(T["hotel"].upper())}</div>')
    b.append(f'<div style="position:absolute;inset:70px;border:3px solid {GOLD}"></div>')
    css = (font("Alex Brush") + font("Tiro Telugu") + font("Marcellus") +
           f"*{{margin:0;padding:0;box-sizing:border-box}}html,body{{width:{W+2*BLEED}px;height:{H+2*BLEED}px;overflow:hidden}}"
           f"body{{position:relative;background:{IVORY}}}.c{{position:absolute;left:0;right:0;text-align:center}}"
           f"@page{{size:{(W+2*BLEED)/100}in {(H+2*BLEED)/100}in;margin:0}}")
    return (f'<!doctype html><html><head><meta charset="utf-8"><style>{css}</style></head><body>'
            f'<div id="trim" style="position:absolute;left:{BLEED}px;top:{BLEED}px;width:{W}px;height:{H}px">{"".join(b)}</div></body></html>')

(OUT / "reception-flexi.html").write_text(board())
subprocess.run(["node", str(HERE / "render.mjs"), str(OUT), "reception-flexi"], check=True)
