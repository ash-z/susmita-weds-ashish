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
    face = lambda cx, cy, w=1: (f'<path d="M{cx-38*w} {cy-26} q10 -8 22 -2 M{cx+16*w} {cy-28} q12 -6 22 2" fill="none" {o} stroke-width="3.5"/>'
                                f'<ellipse cx="{cx-26*w}" cy="{cy}" rx="6.5" ry="9" fill="{hair}"/><ellipse cx="{cx+26*w}" cy="{cy}" rx="6.5" ry="9" fill="{hair}"/>'
                                f'<circle cx="{cx-46*w}" cy="{cy+32}" r="17" fill="#e8806e" opacity=".42"/><circle cx="{cx+46*w}" cy="{cy+32}" r="17" fill="#e8806e" opacity=".42"/>'
                                f'<path d="M{cx-3} {cy+12} q5 14 -2 20" fill="none" {o} stroke-width="2.4"/>')
    pais = ('<pattern id="jk" width="46" height="56" patternUnits="userSpaceOnUse"><rect width="46" height="56" fill="#e7e9f1"/>'
            '<path d="M10 22 c0 -8 8 -12 14 -9 c7 3 8 12 2 16 c-6 3 -14 0 -16 -7 z" fill="#bfc8de"/><circle cx="36" cy="44" r="3" fill="#bfc8de"/></pattern>'
            '<pattern id="sr" width="44" height="44" patternUnits="userSpaceOnUse"><rect width="44" height="44" fill="#bdd5a8"/>'
            '<circle cx="11" cy="11" r="3.4" fill="#c9a24a"/><circle cx="33" cy="33" r="3.4" fill="#c9a24a"/></pattern>')
    # both drawn full and round: broad shoulders, soft middles, full arms and faces
    a = [  # Ashish, centre x 330
        f'<path d="M240 1050 L326 1050 L320 1500 L258 1500 Z" fill="#9aa6c6" {o}/><path d="M334 1050 L420 1050 L402 1500 L340 1500 Z" fill="#9aa6c6" {o}/>',
        f'<path d="M264 1440 q26 6 52 0 M264 1462 q26 6 52 0 M344 1440 q26 6 52 0 M344 1462 q26 6 52 0" fill="none" stroke="#7d89aa" stroke-width="2.4"/>',
        f'<path d="M258 1500 C246 1514 234 1532 246 1546 L324 1546 C328 1528 324 1508 320 1500 Z" fill="#f0e3c6" {o}/>',
        f'<path d="M340 1500 C336 1508 332 1528 336 1546 L414 1546 C426 1532 414 1514 402 1500 Z" fill="#f0e3c6" {o}/>',
        f'<path d="M244 430 C206 444 192 494 190 560 C184 680 158 800 164 900 C170 980 184 1030 190 1066 C262 1088 398 1088 470 1066 '
        f'C476 1030 490 980 496 900 C502 800 476 680 470 560 C468 494 454 444 416 430 Z" fill="#a9b4d2" {o}/>',
        f'<path d="M240 434 C196 446 170 494 164 562 C156 670 150 780 152 884 L206 890 C206 790 210 690 220 610 Z" fill="#a9b4d2" {o}/>',
        f'<path d="M420 434 C464 446 490 494 496 562 C504 670 510 780 508 884 L454 890 C454 790 450 690 440 610 Z" fill="#a9b4d2" {o}/>',
        f'<ellipse cx="179" cy="918" rx="28" ry="33" fill="{skin_a}" {o}/><ellipse cx="481" cy="918" rx="28" ry="33" fill="{skin_a}" {o}/>',
        f'<path d="M248 432 C226 470 214 530 212 600 C208 700 210 790 216 858 C264 872 308 874 328 872 L328 452 L300 430 Z" fill="url(#jk)" {o}/>',
        f'<path d="M412 432 C434 470 446 530 448 600 C452 700 450 790 444 858 C396 872 352 874 332 872 L332 452 L360 430 Z" fill="url(#jk)" {o}/>',
        "".join(f'<circle cx="338" cy="{y}" r="6" fill="#c9a24a" stroke="{LINE}" stroke-width="1.6"/>' for y in range(500, 860, 64)),
        f'<path d="M298 366 L298 420 C318 434 342 434 362 420 L362 366 Z" fill="{skin_a}" {o}/>',
        f'<path d="M294 424 C312 440 348 440 366 424 L364 404 C346 414 314 414 296 404 Z" fill="#e7e9f1" {o}/>',
        f'<ellipse cx="236" cy="286" rx="15" ry="23" fill="{skin_a}" {o}/><ellipse cx="424" cy="286" rx="15" ry="23" fill="{skin_a}" {o}/>',
        f'<ellipse cx="330" cy="282" rx="96" ry="98" fill="{skin_a}" {o}/>',
        # beard along the jaw from the sideburns, a moustache with lifted tips, the smile showing under it
        f'<path d="M240 258 C232 308 246 360 292 390 C310 400 350 400 368 390 C414 360 428 308 420 258 L410 258 C410 304 396 338 366 350 '
        f'C348 356 312 356 294 350 C264 338 250 304 250 258 Z" fill="{hair}" {o} stroke-width="2.4"/>',
        f'<path d="M302 337 C312 329 324 329 330 334 C336 329 348 329 358 337 C348 336 340 338 330 339 C320 338 312 336 302 337 Z" fill="{hair}"/>',
        f'<path d="M316 356 q14 10 28 0" fill="none" stroke="#f3d2c4" stroke-width="3.5" stroke-linecap="round"/>',
        # short hair: a side-swept top with volume, a soft hairline, cut close above the ears
        f'<path d="M242 264 C224 194 262 142 330 136 C402 132 446 180 420 264 C416 238 404 220 382 212 C356 204 326 206 304 186 '
        f'C300 208 278 218 264 230 C254 240 246 252 242 264 Z" fill="{hair}" {o}/>',
        f'<path d="M292 164 C326 146 376 148 404 172" fill="none" stroke="#4d3d36" stroke-width="3"/>',
        face(330, 280, 1.12),
        f'<ellipse cx="330" cy="226" rx="5" ry="10" fill="#c8323c"/>',
        garland((282, 440), (378, 440), (330, 884)),
    ]
    s = [  # Sai Susmita, centre x 670
        f'<path d="M742 512 C786 540 808 700 818 1120 L776 1112 C768 800 760 620 734 540 Z" fill="#e7a0b5" {o}/>',
        f'<path d="M776 1112 L818 1120" stroke="#c9a24a" stroke-width="10"/>',
        f'<path d="M572 830 C556 1000 542 1300 532 1530 C604 1552 736 1552 808 1530 C798 1300 784 1000 768 830 Z" fill="url(#sr)" {o}/>',
        "".join(f'<path d="M{x0} 850 L{x1} 1534" stroke="#9cb987" stroke-width="3"/>' for x0, x1 in ((648, 620), (660, 644), (672, 670), (684, 696), (696, 722))),
        f'<path d="M538 1504 C604 1524 736 1524 802 1504" fill="none" stroke="#e48aa5" stroke-width="16"/><path d="M540 1490 C606 1510 734 1510 800 1490" fill="none" stroke="#c9a24a" stroke-width="5"/>',
        f'<path d="M582 700 C630 716 710 716 758 700 L770 802 C712 818 628 818 570 802 Z" fill="url(#sr)" {o}/>',
        f'<path d="M600 522 C578 544 574 604 578 644 L584 704 C630 718 710 718 756 704 L762 644 C766 604 762 544 740 522 C706 506 634 506 600 522 Z" fill="#d97f9b" {o}/>',
        f'<path d="M568 798 C628 814 712 814 772 798 L774 834 C712 850 628 850 566 834 Z" fill="#d8b25a" {o}/>',
        f'<path d="M572 766 L620 806 C668 706 716 606 752 532 L726 512 C692 592 630 690 572 766 Z" fill="#e7a0b5" {o}/>',
        f'<path d="M582 772 C630 694 682 600 718 520 M612 800 C662 702 712 606 744 536" fill="none" stroke="#c9a24a" stroke-width="5"/>',
        f'<path d="M602 524 C572 532 558 566 554 606 L548 664 L594 672 L600 608 Z" fill="#d97f9b" {o}/>',
        f'<path d="M738 524 C768 532 782 566 786 606 L792 664 L746 672 L740 608 Z" fill="#d97f9b" {o}/>',
        f'<path d="M549 662 L595 670 C608 714 636 766 670 794 L646 822 C598 788 560 722 549 662 Z" fill="{skin_s}" {o}/>',
        f'<path d="M791 662 L745 670 C732 714 704 766 670 794 L694 822 C742 788 780 722 791 662 Z" fill="{skin_s}" {o}/>',
        "".join(f'<path d="M{x} {y} l{dx} {dy}" stroke="{c}" stroke-width="7" stroke-linecap="round"/>' for x, y, dx, dy, c in (
            (608, 760, 24, -18, "#c8323c"), (614, 771, 24, -18, "#c9a24a"), (620, 782, 24, -18, "#c8323c"),
            (732, 760, -24, -18, "#c8323c"), (726, 771, -24, -18, "#c9a24a"), (720, 782, -24, -18, "#c8323c"))),
        f'<ellipse cx="670" cy="810" rx="44" ry="29" fill="{skin_s}" {o}/>',
        "".join(f'<circle cx="{x}" cy="{y}" r="3" fill="#a0522d"/>' for x, y in ((654, 804), (670, 800), (686, 804), (660, 817), (680, 817))),
        f'<path d="M640 488 L640 524 C656 536 684 536 700 524 L700 488 Z" fill="{skin_s}" {o}/>',
        f'<path d="M636 516 C646 558 694 558 704 516" fill="none" stroke="#c9a24a" stroke-width="8"/><circle cx="670" cy="558" r="10" fill="#c9a24a" stroke="{LINE}" stroke-width="2"/>',
        f'<circle cx="756" cy="452" r="46" fill="{hair}" {o}/>',
        "".join(f'<circle cx="{756+52*math.cos(math.radians(t)):.1f}" cy="{452+52*math.sin(math.radians(t)):.1f}" r="8" fill="#fffdf8" stroke="#9c8b7c" stroke-width="1.6"/>' for t in range(-70, 100, 17)),
        f'<path d="M582 420 C575 326 620 302 670 302 C720 302 765 326 758 420 C755 456 745 472 740 486 L600 486 C590 472 585 456 582 420 Z" fill="{hair}" {o}/>',
        f'<ellipse cx="586" cy="426" rx="13" ry="20" fill="{skin_s}" {o}/><ellipse cx="754" cy="426" rx="13" ry="20" fill="{skin_s}" {o}/>',
        f'<ellipse cx="670" cy="416" rx="88" ry="86" fill="{skin_s}" {o}/>',
        f'<path d="M584 414 C580 350 615 314 670 314 C725 314 760 350 756 414 C748 380 724 360 692 352 C681 349 672 344 670 334 C668 344 659 349 648 352 C616 360 592 380 584 414 Z" fill="{hair}" {o}/>',
        face(670, 420, 1.1),
        f'<path d="M652 466 q18 13 36 0" fill="none" {o}/>',
        f'<circle cx="670" cy="378" r="6.5" fill="#c8323c"/>',
        "".join(f'<path d="M{x} 444 l0 10 M{x-12} 472 C{x-12} 454 {x+12} 454 {x+12} 472 Z" fill="#c9a24a" stroke="#a07a2a" stroke-width="2.4"/>' for x in (586, 754)),
        garland((628, 532), (712, 532), (670, 766), n=28),
    ]
    # widen the bodies and faces about each figure's centre (strokes stay even)
    wide = lambda cx, k, dx=0: f'<g transform="translate({cx + dx} 0) scale({k} 1) translate({-cx} 0)">'
    ashish = (wide(330, 1.14) + "".join(a[:13]) + "</g>" + wide(330, 1.08) + "".join(a[13:22]) + "</g>" + wide(330, 1.14) + a[22] + "</g>")
    susmita = (wide(670, 1.1, 18) + "".join(s[:19]) + "</g>" + wide(670, 1.06, 18) + "".join(s[19:29]) + "</g>" + wide(670, 1.1, 18) + s[29] + "</g>")
    return (f'<svg viewBox="70 120 860 1450" width="100%" height="100%" style="overflow:visible"><defs>{pais}</defs>'
            f'<ellipse cx="500" cy="1552" rx="420" ry="16" fill="#7c5a4a" opacity=".12"/>{ashish}{susmita}</svg>')

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
    b.append(f'<div style="position:absolute;left:{(W-1139)/2}px;top:950px;width:1139px;height:1920px">{couple()}</div>')
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
