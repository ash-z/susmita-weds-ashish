"""The invitation as a poster: one self-contained SVG per invitation, a PNG of it (WhatsApp and phones don't
preview SVG), and a small page to view, save and share it.

    cd invite-src && <python with segno> poster/poster.py      (needs network once to cache the fonts, and node +
                                                               Playwright's Chromium for the PNG; see HANDOFF.md)

Writes docs/poster/ (relatives), docs/friends/poster/ and docs/bhimanpalliwar/poster/: index.html, poster.svg, poster.png.
The wording and details here are a copy of body.html's: change them in both places.
"""
import base64, hashlib, html, json, pathlib, re, subprocess, urllib.request
import segno

here = pathlib.Path(__file__).resolve().parent
src, root = here.parent, here.parent.parent
fonts_dir = here / "fonts"; fonts_dir.mkdir(exist_ok=True)

W = 1080
INK, GOLD, ACCENT, MUTED, GANESHA = "#2B2318", "#826019", "#9A3A32", "#6B5B47", "#8A2C22"

BRIDE_PARENTS, GROOM_PARENTS = "Chandrika & Srinivasulu Gorantla", "Satyarani & Suresh Bhimanpalliwar"
WEDDING = dict(label="THE WEDDING", day="Thursday, 29 October 2026", time="7:31 PM", note="Sumuhurtam",
               venue="Hotel Ambica Sea Green", hall="‘Marina’ Banquet Hall", addr=["Beach Road,", "Visakhapatnam"])
RECEPTION = dict(label="THE RECEPTION", day="Sunday, 1 November 2026", time="12:00 PM", note="onwards",
                 venue="Hotel Tulip Grand", hall="‘Vedha’ · 5th floor", addr=["Annojiguda,", "Hyderabad"])
DAY_BEFORE = dict(label="THE DAY BEFORE · WEDNESDAY, 28 OCTOBER 2026",
                  rows=[("9:00 AM onwards", "Haldi & Pellikuturu"), ("5:00 PM onwards", "Mehendi")],
                  where=["Home · 9-6-93/3, Sivajipalem,", "Opp. Sivaji Park, Visakhapatnam"])
VARIANTS = {
    "relatives": dict(path="", names=("Sai Susmita", "Ashish"), parents=(BRIDE_PARENTS, GROOM_PARENTS), day_before=False),
    "friends":   dict(path="friends/", names=("Sai Susmita", "Ashish"), parents=(BRIDE_PARENTS, GROOM_PARENTS), day_before=True),
    "groom":     dict(path="bhimanpalliwar/", names=("Ashish", "Sai Susmita"), parents=(GROOM_PARENTS, BRIDE_PARENTS), day_before=False),
}
SITE = "https://susmitawedsashish.in/"

def b64(path, kind="image/webp"):
    return f"data:{kind};base64," + base64.b64encode(pathlib.Path(path).read_bytes()).decode()

def esc(t): return html.escape(t, quote=False)

# ---------- fonts: Google Fonts subsets for exactly the text used, cached in poster/fonts ----------
def font_face(family, weight, text):
    key = hashlib.sha1(f"{family}|{weight}|{''.join(sorted(set(text)))}".encode()).hexdigest()[:12]
    f = fonts_dir / f"{family.replace(' ', '')}-{weight}-{key}.woff2"
    if not f.exists():
        q = family.replace(" ", "+") + (f":wght@{weight}" if weight != 400 else "")
        url = f"https://fonts.googleapis.com/css2?family={q}&text={urllib.parse.quote(''.join(sorted(set(text))))}"
        css = urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36"})).read().decode()
        woff = re.search(r"src: url\((https://[^)]+)\)", css).group(1)
        f.write_bytes(urllib.request.urlopen(woff).read())
    return (f"@font-face{{font-family:'P {family}';font-weight:{weight};"
            f"src:url(data:font/woff2;base64,{base64.b64encode(f.read_bytes()).decode()}) format('woff2')}}")

# ---------- the poster ----------
class Svg:
    def __init__(self): self.parts, self.text = [], {}
    def add(self, s): self.parts.append(s)
    def t(self, x, y, s, fam, size, fill=INK, weight=400, anchor="middle", spacing=0, opacity=1):
        self.text.setdefault((fam, weight), []).append(s)
        sp = f' letter-spacing="{spacing}"' if spacing else ""
        op = f' opacity="{opacity}"' if opacity != 1 else ""
        self.add(f'<text x="{x}" y="{y}" font-family="\'P {fam}\'" font-weight="{weight}" font-size="{size}" '
                 f'fill="{fill}" text-anchor="{anchor}"{sp}{op}>{esc(s)}</text>')

def ornament(s, y, w=180):
    c = W / 2
    s.add(f'<g stroke="{GOLD}" stroke-width="1.6" opacity=".7"><line x1="{c-w}" y1="{y}" x2="{c-16}" y2="{y}"/>'
          f'<line x1="{c+16}" y1="{y}" x2="{c+w}" y2="{y}"/></g>'
          f'<path d="M{c} {y-7} L{c+7} {y} L{c} {y+7} L{c-7} {y} Z" fill="{GOLD}" opacity=".85"/>')

def event_col(s, cx, y, e):
    s.t(cx, y, e["label"], "Karla", 19, GOLD, 600, spacing=4)
    s.t(cx, y + 46, e["day"], "Marcellus", 27, INK)
    s.t(cx, y + 106, e["time"], "Marcellus", 52, GOLD)
    s.t(cx, y + 138, e["note"], "Karla", 19, MUTED, 500, spacing=2)
    s.t(cx, y + 192, e["venue"], "Tiro Telugu", 30, INK)
    s.t(cx, y + 228, e["hall"], "Tiro Telugu", 25, GOLD)
    for i, a in enumerate(e["addr"]): s.t(cx, y + 266 + i * 28, a, "Karla", 20, MUTED, 500)
    return y + 266 + 28 * len(e["addr"])

def poster(v):
    c, s = W / 2, Svg()
    url = SITE + v["path"]
    y = 0
    # garland across the top: the toranam, repeated outward from the centre one (as on the pages), Ganesha in its gap
    tw = 660; th = round(tw * 453 / 1281)
    tor = b64(src / "art/toranam.webp")
    for x in (c - tw / 2 - tw, c - tw / 2, c + tw / 2):
        s.add(f'<image href="{tor}" x="{x}" y="0" width="{tw}" height="{th}"/>')
    gw = round(tw * .105); gh = round(gw * 510 / 392)
    s.add(f'<mask id="gm" style="mask-type:alpha"><image href="{b64(src / "art/ganesha.webp")}" x="{c - gw/2}" y="{round(tw*.028)}" width="{gw}" height="{gh}"/></mask>'
          f'<rect x="{c - gw/2}" y="{round(tw*.028)}" width="{gw}" height="{gh}" fill="{GANESHA}" mask="url(#gm)"/>')
    y = th + 44
    s.t(c, y, "॥ శ్రీ గణేశాయ నమః ॥", "Tiro Telugu", 30, ACCENT)
    # the photograph in an arch, as on the cover
    pw, ph = 280, 344; px, py = c - pw / 2, y + 30
    arch = f"M{px} {py + pw/2} A{pw/2} {pw/2} 0 0 1 {px + pw} {py + pw/2} V{py + ph} H{px} Z"
    s.add(f'<clipPath id="ac"><path d="{arch}"/></clipPath>'
          f'<image href="{b64(src / "photos/out/cover.webp")}" x="{px}" y="{py}" width="{pw}" height="{ph}" preserveAspectRatio="xMidYMid slice" clip-path="url(#ac)"/>'
          f'<path d="{arch}" fill="none" stroke="#A97C2B" stroke-width="3"/>')
    o = 12; arch2 = f"M{px-o} {py + pw/2} A{pw/2+o} {pw/2+o} 0 0 1 {px + pw + o} {py + pw/2} V{py + ph + o} H{px-o} Z"
    s.add(f'<path d="{arch2}" fill="none" stroke="#A97C2B" stroke-width="1.4" opacity=".55"/>')
    y = py + ph + o + 56
    s.t(c, y, "శుభలేఖ", "Tiro Telugu", 38, GOLD)
    s.t(c, y + 40, "WEDDING INVITATION", "Marcellus", 21, MUTED, spacing=6)
    y += 104
    s.t(c, y, "Together with our families, we invite you", "Tiro Telugu", 29, INK)
    s.t(c, y + 38, "to celebrate the wedding of", "Tiro Telugu", 29, INK)
    y += 140
    s.t(c, y, v["names"][0], "Alex Brush", 118, INK)
    s.t(c, y + 54, "&", "Marcellus", 38, GOLD)
    s.t(c, y + 150, v["names"][1], "Alex Brush", 118, INK)
    y += 200
    ornament(s, y)
    y += 58
    if v["day_before"]:
        d = DAY_BEFORE
        s.t(c, y, d["label"], "Karla", 19, GOLD, 600, spacing=3)
        for i, (when, what) in enumerate(d["rows"]):
            s.t(c - 20, y + 50 + i * 44, when, "Marcellus", 27, GOLD, anchor="end")
            s.t(c + 20, y + 50 + i * 44, what, "Tiro Telugu", 30, INK, anchor="start")
        for i, line in enumerate(d["where"]): s.t(c, y + 146 + i * 28, line, "Karla", 20, MUTED, 500)
        y += 226
        ornament(s, y, 120)
        y += 60
    end = max(event_col(s, W * .25 + 6, y, WEDDING), event_col(s, W * .75 - 6, y, RECEPTION))
    s.add(f'<line x1="{c}" y1="{y - 14}" x2="{c}" y2="{end - 10}" stroke="{GOLD}" stroke-width="1.2" opacity=".35"/>')
    y = end + 52
    ornament(s, y - 18, 120)
    y += 34
    s.t(c, y, "With the blessings of", "Tiro Telugu", 25, MUTED)
    s.t(c, y + 42, v["parents"][0], "Marcellus", 27, INK)
    s.t(c, y + 80, v["parents"][1], "Marcellus", 27, INK)
    y += 120
    # QR code to this invitation, flanked by the corner florals
    q = segno.make(url, error="m"); mat = q.matrix; n = len(mat); qs = 180; m = qs / (n + 4)
    qx, qy = c - qs / 2, y
    path = "".join(f"M{qx + (j + 2) * m:.2f} {qy + (i + 2) * m:.2f}h{m:.2f}v{m:.2f}h{-m:.2f}z"
                   for i, row in enumerate(mat) for j, cell in enumerate(row) if cell)
    s.add(f'<rect x="{qx}" y="{qy}" width="{qs}" height="{qs}" rx="10" fill="#FFFCF6" stroke="#A97C2B" stroke-opacity=".45"/>'
          f'<path d="{path}" fill="{INK}"/>')
    s.t(c, qy + qs + 40, "Scan for the invitation, RSVP & directions", "Karla", 20, MUTED, 500)
    s.t(c, qy + qs + 78, url.replace("https://", "").rstrip("/"), "Marcellus", 27, GOLD, spacing=1)
    H = round(qy + qs + 140)
    cw = 210
    s.add(f'<image href="{b64(src / "art/corner-left.webp")}" x="0" y="{H - cw * 462 / 412:.0f}" width="{cw}" height="{cw * 462 / 412:.0f}"/>'
          f'<image href="{b64(src / "art/corner-right.webp")}" x="{W - cw}" y="{H - cw * 445 / 398:.0f}" width="{cw}" height="{cw * 445 / 398:.0f}"/>')
    faces = "".join(font_face(f, w, "".join(t)) for (f, w), t in s.text.items())
    head = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}">'
            f'<title>{esc(v["names"][0])} weds {esc(v["names"][1])}: wedding invitation</title>'
            f'<style>{faces}</style>'
            f'<defs><radialGradient id="bg" cx="50%" cy="38%" r="75%"><stop offset="0" stop-color="#FFFCF6"/>'
            f'<stop offset=".55" stop-color="#F7F2E8"/><stop offset="1" stop-color="#EFE6D5"/></radialGradient></defs>'
            f'<rect width="{W}" height="{H}" fill="url(#bg)"/>'
            f'<rect x="22" y="22" width="{W-44}" height="{H-44}" rx="18" fill="none" stroke="#A97C2B" stroke-opacity=".35" stroke-width="1.5"/>')
    return head + "".join(s.parts) + "</svg>", H

def page(v, H):
    title = f'{v["names"][0]} weds {v["names"][1]}'
    url = SITE + v["path"]
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)}: poster</title>
<meta property="og:type" content="website">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="Our wedding invitation. Save the poster, or open the invitation.">
<meta property="og:url" content="{url}poster/">
<meta property="og:image" content="{url}poster/poster.png">
<meta name="theme-color" content="#F7F2E8">
<style>
  :root{{color-scheme:light}}
  body{{margin:0;background:#EFE6D5;color:#2B2318;font:500 15px/1.5 Karla,system-ui,sans-serif;text-align:center}}
  main{{max-width:560px;margin:0 auto;padding:16px 16px 32px}}
  img{{display:block;width:100%;height:auto;border-radius:14px;box-shadow:0 24px 50px -20px rgba(70,45,15,.42);background:#F7F2E8}}
  .row{{display:flex;flex-wrap:wrap;gap:10px;justify-content:center;margin-top:18px}}
  a,button{{display:inline-flex;align-items:center;justify-content:center;min-height:46px;padding:0 20px;border-radius:14px;
    font:600 13px/1 Karla,system-ui,sans-serif;letter-spacing:.1em;text-transform:uppercase;text-decoration:none;cursor:pointer;
    border:1px solid rgba(169,124,43,.45);background:#FFFCF6;color:#826019}}
  .solid{{background:#826019;color:#FFFCF6;border-color:#826019}}
  p{{margin:14px 0 0;color:#6B5B47;font-size:14px}}
</style>
</head>
<body>
<main>
  <img src="poster.png" width="{W}" height="{H}" alt="{esc(title)}: wedding invitation poster. Wedding on Thursday 29 October 2026, 7:31 PM, at Hotel Ambica Sea Green, Visakhapatnam; reception on Sunday 1 November 2026, 12 PM onwards, in the Vedha hall of Hotel Tulip Grand, Hyderabad.">
  <div class="row">
    <a class="solid" href="poster.png" download="{title.replace(' ', '-')}-invitation.png">Save poster</a>
    <button id="share" type="button" hidden>Share</button>
    <a href="{url}">Open invitation</a>
  </div>
  <p>Print-quality version: <a href="poster.svg" download style="all:unset;color:#826019;text-decoration:underline;cursor:pointer">SVG</a></p>
</main>
<script>
(function(){{
  var b = document.getElementById('share'); if(!navigator.share) return; b.hidden = false;
  b.addEventListener('click', function(){{
    fetch('poster.png').then(function(r){{ return r.blob(); }}).then(function(blob){{
      var f = new File([blob], {json.dumps(title.replace(' ', '-') + '-invitation.png')}, {{type:'image/png'}});
      var d = {{ title:{json.dumps(title)}, text:{json.dumps(title + ' — our wedding invitation: ' + url)}, files:[f] }};
      if(navigator.canShare && navigator.canShare(d)) return navigator.share(d);
      return navigator.share({{ title:d.title, text:d.text, url:location.href }});
    }}).catch(function(){{}});
  }});
}})();
</script>
</body>
</html>
"""

out = []
for name, v in VARIANTS.items():
    svg, H = poster(v)
    d = root / "docs" / v["path"] / "poster"; d.mkdir(parents=True, exist_ok=True)
    (d / "poster.svg").write_text(svg)
    (d / "index.html").write_text(page(v, H))
    out.append((name, d, H))
# PNG of each SVG, rendered by Chromium at 1.5x (1620px wide) so text and the photo stay crisp when shared
render = here / "render.mjs"
subprocess.run(["node", str(render)] + [f"{d}/poster.svg:{H}" for _, d, H in out], check=True)
for name, d, H in out:
    print(f"{name:10} {d.relative_to(root)}: poster.svg {(d/'poster.svg').stat().st_size//1024} KB, poster.png {(d/'poster.png').stat().st_size//1024} KB, 1080x{H}")
