"""The reception's welcome board in a soft illustrated style: 24 x 36 in (2 x 3 ft), portrait.

    python3 invite-src/signage/reception_floral.py    # -> invite-src/signage/out/reception-floral.{html,png,pdf}

Blush paper, pastel lotus / jasmine / lotus-leaf clusters running off the edges (the lotus garlands and backdrop of
the engagement), and the couple drawn flat in a simple line style, dressed as at the engagement: Ashish in the
grey-blue kurta and silver brocade jacket, Sai Susmita in the green silk saree with the pink pallu. Everything is
vector, so it prints crisp at board size. Same wording as reception_sign.py (groom first, at the couple's request).
"""
import base64, html, math, subprocess
import common
from common import W, H, BLEED, OUT, HERE

T = dict(te="రిసెప్షన్", heading="Reception", bride="Sai Susmita", groom="Ashish",
         when="Sunday · 1 November 2026 · 12:00 PM onwards", hotel="Hotel Tulip Grand", hall="‘Vedha’ · 5th Floor")
E = lambda s: html.escape(s, quote=False)
TEXT = "".join(sorted(set(" ".join(T.values()) + " &·‘’0123456789 ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz")))
def font(family, weight=400): return common.font(family, weight, TEXT)

# colours inside the CMYK gamut; dark enough type to read outdoors on the light board
PAPER, PAPER_LO = "#fbf1ec", "#f3e0d8"
INK = "#4b3530"                            # small type
ROSE = "#7c3a46"                           # names and the hall
LINE = "#4a3228"                           # the illustration's outline

# ---------------- flowers ----------------
DEFS = """
<linearGradient id="pt" x1="0" y1="1" x2="0" y2="0"><stop offset="0" stop-color="#fdeef1"/><stop offset=".55" stop-color="#f6c9d4"/><stop offset="1" stop-color="#e48aa3"/></linearGradient>
<linearGradient id="pd" x1="0" y1="1" x2="0" y2="0"><stop offset="0" stop-color="#f8d7df"/><stop offset=".6" stop-color="#ec9fb4"/><stop offset="1" stop-color="#d4678a"/></linearGradient>
<radialGradient id="pad" cx=".5" cy=".5" r=".55"><stop offset="0" stop-color="#c9d8b9"/><stop offset=".7" stop-color="#a8bf98"/><stop offset="1" stop-color="#8eab82"/></radialGradient>
<linearGradient id="lf" x1="0" y1="1" x2="0" y2="0"><stop offset="0" stop-color="#8eab82"/><stop offset="1" stop-color="#bccfae"/></linearGradient>
<radialGradient id="wh" cx=".5" cy=".7" r=".7"><stop offset="0" stop-color="#ffffff"/><stop offset="1" stop-color="#f1e8df"/></radialGradient>
<radialGradient id="bl" cx=".5" cy=".9" r=".9"><stop offset="0" stop-color="#fdf0ec"/><stop offset="1" stop-color="#efbcb4"/></radialGradient>
"""
PETAL = "M0 0 C -34 -40 -32 -112 0 -150 C 32 -112 34 -40 0 0 Z"

def g(x, y, s, rot, body): return f'<g transform="translate({x} {y}) rotate({rot}) scale({s})">{body}</g>'

def lotus(x, y, s=1, rot=0):
    """an open lotus seen from the side: a fan of petals, the inner ones deeper pink"""
    back = "".join(f'<path d="{PETAL}" transform="rotate({a}) scale(.9 1)" fill="url(#pt)"/>' for a in (-78, -50, 50, 78))
    mid = "".join(f'<path d="{PETAL}" transform="rotate({a}) scale(1 1.05)" fill="url(#pt)"/>' for a in (-24, 24))
    front = "".join(f'<path d="{PETAL}" transform="rotate({a}) scale(.85 .82)" fill="url(#pd)"/>' for a in (-40, 0, 40))
    veins = "".join(f'<path d="M0 -14 L0 -110" transform="rotate({a}) scale(.85 .82)" stroke="#d9849b" stroke-width="2" opacity=".5"/>' for a in (-40, 0, 40))
    return g(x, y, s, rot, f'<g stroke="#dc8fa4" stroke-width="1.6">{back}{mid}{front}</g>{veins}'
                           '<ellipse cx="0" cy="-8" rx="30" ry="12" fill="#e9c46a"/>')

def bud(x, y, s=1, rot=0):
    return g(x, y, s, rot, '<path d="M0 0 C 4 60 2 120 -6 190" stroke="#8aa77e" stroke-width="7" fill="none"/>'
                           '<path d="M0 0 C -30 -34 -26 -90 0 -128 C 26 -90 30 -34 0 0 Z" fill="url(#pd)" stroke="#d47f97" stroke-width="1.6"/>'
                           '<path d="M0 0 C -14 -30 -10 -70 0 -100" stroke="#cf7690" stroke-width="2" fill="none" opacity=".6"/>')

def pad(x, y, r, rot=0):
    """a lotus leaf: a disc with a notch, veins from the centre"""
    pts = []
    for k in range(73):
        a = math.radians(14 + k * (332 / 72))
        wob = 1 + .025 * math.sin(k * 1.7)
        pts.append(f"{r * wob * math.cos(a):.1f} {r * wob * math.sin(a):.1f}")
    veins = "".join(f'<path d="M0 0 L{r*.92*math.cos(math.radians(a)):.1f} {r*.92*math.sin(math.radians(a)):.1f}"/>' for a in range(40, 360, 28))
    return g(x, y, 1, rot, f'<path d="M0 0 L{" L".join(pts)} Z" fill="url(#pad)" stroke="#86a37a" stroke-width="2"/>'
                           f'<g stroke="#e3ecd8" stroke-width="3" opacity=".7">{veins}</g>')

def leaf(x, y, s=1, rot=0):
    return g(x, y, s, rot, '<path d="M0 0 C 30 -44 30 -110 0 -165 C -30 -110 -30 -44 0 0 Z" fill="url(#lf)" stroke="#86a37a" stroke-width="1.6"/>'
                           '<path d="M0 -6 L0 -150" stroke="#e3ecd8" stroke-width="2.5" opacity=".8"/>')

def jasmine(x, y, s=1, rot=0):
    p = "".join(f'<ellipse cx="0" cy="-19" rx="9.5" ry="19" transform="rotate({a})"/>' for a in range(0, 360, 72))
    return g(x, y, s, rot, f'<g fill="url(#wh)" stroke="#e2d6c8" stroke-width="1.4">{p}</g><circle r="4.5" fill="#efd27c"/>')

def blossom(x, y, s=1, rot=0):
    """a small blush five-petalled flower with a yellow heart"""
    p = "".join(f'<circle cx="0" cy="-30" r="32" transform="rotate({a})"/>' for a in range(0, 360, 72))
    dots = "".join(f'<circle cx="{12*math.cos(math.radians(a)):.1f}" cy="{12*math.sin(math.radians(a)):.1f}" r="3.2"/>' for a in range(0, 360, 40))
    return g(x, y, s, rot, f'<g fill="url(#bl)" stroke="#e7aaa2" stroke-width="1.6">{p}</g>'
                           f'<circle r="14" fill="#efce6d"/><g fill="#c99a3a">{dots}</g>')

def corner():
    """a cluster for the top-left corner, running off both edges; mirrored for the other corners"""
    return (pad(70, 120, 250, 30) + pad(380, -40, 170, 200) + leaf(350, 230, 1.5, 115) + leaf(150, 430, 1.6, 160) +
            leaf(470, 120, 1.2, 95) + lotus(250, 280, 1.55, 135) + bud(520, 210, 1.05, 112) + bud(90, 560, 1.0, 175) +
            blossom(60, 330, 1.25, 10) + blossom(470, 30, 1.0, 40) + blossom(330, 430, .85, 20) +
            "".join(jasmine(x, y, 1.15, r) for x, y, r in ((560, 330, 10), (600, 280, 40), (420, 380, 60), (210, 520, 20), (30, 470, 50))))

def side():
    """a smaller cluster for the middle of a long edge"""
    return (pad(-60, 0, 200, 0) + leaf(40, -190, 1.4, 50) + leaf(60, 170, 1.3, 125) + lotus(70, 20, 1.2, 92) +
            bud(150, -120, .9, 70) + blossom(-10, 230, .9, 0) +
            "".join(jasmine(x, y, 1.05, r) for x, y, r in ((190, 60, 0), (160, 120, 30), (140, -40, 50))))

def flowers():
    return (f'<svg width="{W}" height="{H}" style="position:absolute;left:0;top:0;overflow:visible"><defs>{DEFS}</defs>'
            f'<g>{corner()}</g><g transform="translate({W} 0) scale(-1 1)">{corner()}</g>'
            f'<g transform="translate(0 {H}) scale(1 -1)">{corner()}</g><g transform="translate({W} {H}) scale(-1 -1)">{corner()}</g>'
            f'<g transform="translate(0 1560)">{side()}</g><g transform="translate({W} 2050) scale(-1 1)">{side()}</g></svg>')

# ---------------- the couple ----------------
def bezier(p0, p1, p2, p3, n):
    out = []
    for i in range(n + 1):
        t = i / n; u = 1 - t
        out.append(tuple(u**3 * a + 3 * u * u * t * b + 3 * u * t * t * c + t**3 * d for a, b, c, d in zip(p0, p1, p2, p3)))
    return out

def garland(left, right, low, n=34):
    """a jasmine garland with pink lotus buds, hung from two shoulder points down to a low point"""
    (lx, ly), (rx, ry), (bx, by) = left, right, low
    pts = bezier((lx, ly), (lx - 12, ly + (by - ly) * .55), (bx - 40, by - 30), (bx, by), n // 2) + \
          bezier((bx, by), (bx + 40, by - 30), (rx + 12, ry + (by - ry) * .55), (rx, ry), n // 2)[1:]
    s = []
    for k, (x, y) in enumerate(pts):
        if k % 6 == 3:
            s.append(f'<path d="M{x:.1f} {y-16:.1f} C{x+13:.1f} {y-6:.1f} {x+10:.1f} {y+12:.1f} {x:.1f} {y+18:.1f} '
                     f'C{x-10:.1f} {y+12:.1f} {x-13:.1f} {y-6:.1f} {x:.1f} {y-16:.1f} Z" fill="#e98fa8" stroke="{LINE}" stroke-width="2"/>')
        else:
            s.append(f'<circle cx="{x-5:.1f}" cy="{y:.1f}" r="8" fill="#fffdf8" stroke="#9c8b7c" stroke-width="1.6"/>'
                     f'<circle cx="{x+5:.1f}" cy="{y+3:.1f}" r="8" fill="#fffdf8" stroke="#9c8b7c" stroke-width="1.6"/>')
    tassel = "".join(f'<path d="M{bx+dx} {by+10} C{bx+dx+10} {by+30} {bx+dx+6} {by+52} {bx+dx} {by+60} C{bx+dx-6} {by+52} '
                     f'{bx+dx-10} {by+30} {bx+dx} {by+10} Z" fill="#e98fa8" stroke="{LINE}" stroke-width="2"/>' for dx in (-14, 0, 14))
    return "".join(s) + tassel

def couple():
    """drawn on a 1000 x 1600 canvas (shown cropped to the figures): Ashish on the left (named first), Sai Susmita on the right"""
    o = f'stroke="{LINE}" stroke-width="3" stroke-linejoin="round" stroke-linecap="round"'
    skin_a, skin_s, hair = "#c98d68", "#d6a07f", "#2b1e19"
    face = lambda cx, cy: (f'<path d="M{cx-38} {cy-26} q10 -8 22 -2 M{cx+16} {cy-28} q12 -6 22 2" fill="none" {o} stroke-width="3.5"/>'
                           f'<ellipse cx="{cx-26}" cy="{cy}" rx="6.5" ry="9" fill="{hair}"/><ellipse cx="{cx+26}" cy="{cy}" rx="6.5" ry="9" fill="{hair}"/>'
                           f'<circle cx="{cx-44}" cy="{cy+30}" r="15" fill="#e8806e" opacity=".42"/><circle cx="{cx+44}" cy="{cy+30}" r="15" fill="#e8806e" opacity=".42"/>'
                           f'<path d="M{cx-3} {cy+12} q5 14 -2 20" fill="none" {o} stroke-width="2.4"/>')
    pais = ('<pattern id="jk" width="46" height="56" patternUnits="userSpaceOnUse"><rect width="46" height="56" fill="#e7e9f1"/>'
            '<path d="M10 22 c0 -8 8 -12 14 -9 c7 3 8 12 2 16 c-6 3 -14 0 -16 -7 z" fill="#bfc8de"/><circle cx="36" cy="44" r="3" fill="#bfc8de"/></pattern>'
            '<pattern id="sr" width="44" height="44" patternUnits="userSpaceOnUse"><rect width="44" height="44" fill="#bdd5a8"/>'
            '<circle cx="11" cy="11" r="3.4" fill="#c9a24a"/><circle cx="33" cy="33" r="3.4" fill="#c9a24a"/></pattern>')
    a = [  # Ashish, centre x 330
        f'<path d="M262 1040 L318 1040 L312 1500 L274 1500 Z" fill="#9aa6c6" {o}/><path d="M342 1040 L398 1040 L386 1500 L348 1500 Z" fill="#9aa6c6" {o}/>',
        f'<path d="M276 1440 q18 6 34 0 M276 1462 q18 6 34 0 M350 1440 q18 6 34 0 M350 1462 q18 6 34 0" fill="none" stroke="#7d89aa" stroke-width="2.4"/>',
        f'<path d="M274 1500 C262 1514 250 1532 262 1546 L318 1546 C322 1528 316 1508 312 1500 Z" fill="#f0e3c6" {o}/>',
        f'<path d="M348 1500 C344 1508 338 1528 342 1546 L398 1546 C410 1532 398 1514 386 1500 Z" fill="#f0e3c6" {o}/>',
        f'<path d="M252 432 C222 445 205 480 200 540 L186 862 L228 866 L242 560 Z" fill="#a9b4d2" {o}/>',
        f'<path d="M408 432 C438 445 455 480 460 540 L474 862 L432 866 L418 560 Z" fill="#a9b4d2" {o}/>',
        f'<ellipse cx="206" cy="892" rx="22" ry="30" fill="{skin_a}" {o}/><ellipse cx="454" cy="892" rx="22" ry="30" fill="{skin_a}" {o}/>',
        f'<path d="M255 430 C240 440 230 470 228 520 L214 1060 C272 1076 388 1076 446 1060 L432 520 C430 470 420 440 405 430 Z" fill="#a9b4d2" {o}/>',
        f'<path d="M260 430 C246 470 242 520 242 560 L240 842 C272 852 310 854 328 852 L328 452 L300 430 Z" fill="url(#jk)" {o}/>',
        f'<path d="M400 430 C414 470 418 520 418 560 L420 842 C388 852 350 854 332 852 L332 452 L360 430 Z" fill="url(#jk)" {o}/>',
        "".join(f'<circle cx="338" cy="{y}" r="6" fill="#c9a24a" stroke="{LINE}" stroke-width="1.6"/>' for y in range(500, 830, 64)),
        f'<path d="M305 362 L305 420 C320 432 340 432 355 420 L355 362 Z" fill="{skin_a}" {o}/>',
        f'<path d="M296 424 C312 440 348 440 364 424 L362 404 C346 414 314 414 298 404 Z" fill="#e7e9f1" {o}/>',
        f'<ellipse cx="246" cy="282" rx="14" ry="22" fill="{skin_a}" {o}/><ellipse cx="414" cy="282" rx="14" ry="22" fill="{skin_a}" {o}/>',
        f'<ellipse cx="330" cy="275" rx="86" ry="102" fill="{skin_a}" {o}/>',
        # beard along the jaw from the sideburns, a moustache with lifted tips, the smile showing under it
        f'<path d="M252 258 C246 300 256 350 296 382 C312 392 348 392 364 382 C404 350 414 300 408 258 L400 258 C400 300 388 332 362 344 '
        f'C346 350 314 350 298 344 C272 332 260 300 260 258 Z" fill="{hair}" {o} stroke-width="2.4"/>',
        f'<path d="M302 335 C312 327 324 327 330 332 C336 327 348 327 358 335 C348 334 340 336 330 337 C320 336 312 334 302 335 Z" fill="{hair}"/>',
        f'<path d="M316 354 q14 10 28 0" fill="none" stroke="#f3d2c4" stroke-width="3.5" stroke-linecap="round"/>',
        # short hair: a side-swept top with volume, a soft hairline, cut close above the ears
        f'<path d="M254 262 C240 196 272 148 330 142 C392 138 432 178 414 262 C410 238 400 220 380 212 C356 204 326 206 304 186 '
        f'C300 208 280 218 268 230 C260 240 256 250 254 262 Z" fill="{hair}" {o}/>',
        f'<path d="M296 168 C326 152 372 154 400 176" fill="none" stroke="#4d3d36" stroke-width="3"/>',
        face(330, 278),
        f'<ellipse cx="330" cy="226" rx="5" ry="10" fill="#c8323c"/>',
        garland((284, 438), (376, 438), (330, 870)),
    ]
    s = [  # Sai Susmita, centre x 670
        f'<path d="M732 512 C772 540 792 700 802 1120 L762 1112 C754 800 746 620 724 540 Z" fill="#e7a0b5" {o}/>',
        f'<path d="M762 1112 L802 1120" stroke="#c9a24a" stroke-width="10"/>',
        f'<path d="M600 830 C590 1000 576 1300 562 1530 C622 1550 718 1550 778 1530 C764 1300 750 1000 740 830 Z" fill="url(#sr)" {o}/>',
        "".join(f'<path d="M{x0} 850 L{x1} 1530" stroke="#9cb987" stroke-width="3"/>' for x0, x1 in ((652, 628), (664, 652), (676, 676), (688, 700), (700, 724))),
        f'<path d="M566 1504 C624 1522 716 1522 774 1504" fill="none" stroke="#e48aa5" stroke-width="16"/><path d="M566 1490 C624 1508 716 1508 774 1490" fill="none" stroke="#c9a24a" stroke-width="5"/>',
        f'<path d="M604 700 C640 712 700 712 736 700 L742 800 C700 812 640 812 598 800 Z" fill="url(#sr)" {o}/>',
        f'<path d="M612 520 C598 540 596 600 600 640 L606 702 C640 714 700 714 734 702 L740 640 C744 600 742 540 728 520 C700 505 640 505 612 520 Z" fill="#d97f9b" {o}/>',
        f'<path d="M596 795 C640 808 700 808 744 795 L746 830 C700 843 640 843 594 830 Z" fill="#d8b25a" {o}/>',
        f'<path d="M596 764 L636 802 C680 702 720 602 746 530 L718 512 C690 590 640 690 596 764 Z" fill="#e7a0b5" {o}/>',
        f'<path d="M604 770 C648 694 694 600 724 520 M630 796 C672 700 716 604 742 532" fill="none" stroke="#c9a24a" stroke-width="5"/>',
        f'<path d="M612 522 C590 530 578 560 574 600 L570 652 L606 658 L610 600 Z" fill="#d97f9b" {o}/>',
        f'<path d="M728 522 C750 530 762 560 766 600 L770 652 L734 658 L730 600 Z" fill="#d97f9b" {o}/>',
        f'<path d="M571 650 L605 657 C616 702 642 760 672 790 L652 812 C612 780 580 712 571 650 Z" fill="{skin_s}" {o}/>',
        f'<path d="M769 650 L735 657 C724 702 698 760 668 790 L688 812 C728 780 760 712 769 650 Z" fill="{skin_s}" {o}/>',
        "".join(f'<path d="M{x} {y} l{dx} {dy}" stroke="{c}" stroke-width="7" stroke-linecap="round"/>' for x, y, dx, dy, c in (
            (628, 752, 22, -16, "#c8323c"), (634, 762, 22, -16, "#c9a24a"), (640, 772, 22, -16, "#c8323c"),
            (712, 752, -22, -16, "#c8323c"), (706, 762, -22, -16, "#c9a24a"), (700, 772, -22, -16, "#c8323c"))),
        f'<ellipse cx="670" cy="806" rx="38" ry="26" fill="{skin_s}" {o}/>',
        "".join(f'<circle cx="{x}" cy="{y}" r="3" fill="#a0522d"/>' for x, y in ((656, 800), (670, 796), (684, 800), (662, 812), (678, 812))),
        f'<path d="M646 486 L646 522 C660 532 680 532 694 522 L694 486 Z" fill="{skin_s}" {o}/>',
        f'<path d="M640 512 C650 552 690 552 700 512" fill="none" stroke="#c9a24a" stroke-width="8"/><circle cx="670" cy="552" r="10" fill="#c9a24a" stroke="{LINE}" stroke-width="2"/>',
        f'<circle cx="744" cy="452" r="44" fill="{hair}" {o}/>',
        "".join(f'<circle cx="{744+50*math.cos(math.radians(t)):.1f}" cy="{452+50*math.sin(math.radians(t)):.1f}" r="8" fill="#fffdf8" stroke="#9c8b7c" stroke-width="1.6"/>' for t in range(-70, 100, 17)),
        f'<path d="M592 420 C585 330 625 306 670 306 C715 306 755 330 748 420 C745 456 735 470 730 482 L610 482 C600 470 595 456 592 420 Z" fill="{hair}" {o}/>',
        f'<ellipse cx="596" cy="424" rx="12" ry="19" fill="{skin_s}" {o}/><ellipse cx="744" cy="424" rx="12" ry="19" fill="{skin_s}" {o}/>',
        f'<ellipse cx="670" cy="412" rx="76" ry="88" fill="{skin_s}" {o}/>',
        f'<path d="M594 414 C590 352 620 318 670 318 C720 318 750 352 746 414 C738 382 718 362 690 354 C680 351 672 346 670 336 C668 346 660 351 650 354 C622 362 602 382 594 414 Z" fill="{hair}" {o}/>',
        face(670, 418),
        f'<path d="M654 462 q16 12 32 0" fill="none" {o}/>',
        f'<circle cx="670" cy="376" r="6.5" fill="#c8323c"/>',
        "".join(f'<path d="M{x} 442 l0 10 M{x-12} 470 C{x-12} 452 {x+12} 452 {x+12} 470 Z" fill="#c9a24a" stroke="#a07a2a" stroke-width="2.4"/>' for x in (596, 744)),
        garland((632, 528), (708, 528), (670, 762), n=28),
    ]
    return (f'<svg viewBox="160 120 680 1450" width="100%" height="100%" style="overflow:visible"><defs>{pais}</defs>'
            f'<ellipse cx="500" cy="1552" rx="380" ry="16" fill="#7c5a4a" opacity=".12"/>{"".join(a)}{"".join(s)}</svg>')

def ganesha(x, y, w, h):
    uri = "data:image/svg+xml;base64," + base64.b64encode((HERE / "vector" / "ganesha.svg").read_bytes()).decode()
    return (f'<div style="position:absolute;left:{x}px;top:{y}px;width:{w}px;height:{h}px;background:#b08944;'
            f'-webkit-mask:url({uri}) center/contain no-repeat;mask:url({uri}) center/contain no-repeat"></div>')

def board():
    b = [ganesha(1132, 165, 136, 177)]
    b.append(f'<div class="c" style="top:356px;font-family:\'Tiro Telugu\';font-size:76px;color:#9a7a3e">{E(T["te"])}</div>')
    b.append(f'<div class="c" style="top:468px;font-family:Marcellus;font-size:80px;letter-spacing:22px;text-indent:22px;color:{INK}">{E(T["heading"].upper())}</div>')
    b.append(f'<div class="c" style="top:560px;font-family:\'Alex Brush\';font-size:220px;line-height:1.1;color:{ROSE}">{E(T["groom"])}'
             f'<span style="font-family:Marcellus;font-size:92px;margin:0 46px;vertical-align:middle;color:#b08944">&amp;</span>{E(T["bride"])}</div>')
    b.append(f'<div class="c" style="top:835px;font-family:Marcellus;font-size:62px;letter-spacing:4px;color:{INK}">{E(T["when"])}</div>')
    b.append(f'<div style="position:absolute;left:{(W-900)/2}px;top:950px;width:900px;height:1920px">{couple()}</div>')
    b.append(f'<div class="c" style="top:2905px;font-family:Marcellus;font-size:150px;letter-spacing:3px;color:{ROSE}">{E(T["hall"])}</div>')
    b.append(f'<div class="c" style="top:3118px;font-family:Marcellus;font-size:66px;letter-spacing:12px;text-indent:12px;color:{INK}">{E(T["hotel"].upper())}</div>')
    css = (font("Alex Brush") + font("Tiro Telugu") + font("Marcellus") +
           f"*{{margin:0;padding:0;box-sizing:border-box}}html,body{{width:{W+2*BLEED}px;height:{H+2*BLEED}px;overflow:hidden}}"
           f"body{{position:relative;background:radial-gradient(110% 80% at 50% 42%,{PAPER} 0%,{PAPER} 50%,{PAPER_LO} 100%)}}"
           f".c{{position:absolute;left:0;right:0;text-align:center}}"
           f"@page{{size:{(W+2*BLEED)/100}in {(H+2*BLEED)/100}in;margin:0}}")
    return (f'<!doctype html><html><head><meta charset="utf-8"><style>{css}</style></head><body>'
            f'<div id="trim" style="position:absolute;left:{BLEED}px;top:{BLEED}px;width:{W}px;height:{H}px">{flowers()}{"".join(b)}</div></body></html>')

(OUT / "reception-floral.html").write_text(board())
subprocess.run(["node", str(HERE / "render.mjs"), str(OUT), "reception-floral"], check=True)
