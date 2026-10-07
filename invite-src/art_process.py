"""Turn the Canva workbench previews into transparent art for the invitation.

Each illustration was placed alone on a solid magenta (#FF00FF) page in the
Canva workbench copy (design DAHV9YJ2Iq0). Canva's stored page previews are
downloaded, the magenta is keyed out (with the magenta spill removed from
soft edges), tiles are stitched back together, and the result is trimmed and
saved as WebP in invite-src/art/.

    python3 art_process.py urls.json      # {"page number": "preview url", ...}
"""
import io, json, sys, urllib.request, urllib.parse, pathlib
from PIL import Image
import numpy as np

HERE = pathlib.Path(__file__).resolve().parent
OUT = HERE / "art"
OUT.mkdir(exist_ok=True)

# workbench page -> (name, page width, page height)
PAGES = {
    2: ("peacock", 277, 540),   3: ("diya", 296, 252),
    4: ("couple-a", 416, 406),  5: ("couple-b", 416, 406),
    6: ("gopuram", 375, 450),   7: ("ganesha", 332, 432),
    8: ("corner-left", 429, 505), 9: ("corner-right", 459, 505),
    10: ("toranam-1", 479, 505), 11: ("toranam-2", 479, 505), 12: ("toranam-3", 479, 505),
}

def fetch(url):
    q = urllib.parse.parse_qs(urllib.parse.urlparse(url).query)
    if "fallback" in q:                     # media.canva.com preview -> its signed S3 copy
        url = q["fallback"][0]
    with urllib.request.urlopen(url, timeout=60) as r:
        return Image.open(io.BytesIO(r.read())).convert("RGB")

def key_magenta(img):
    """Alpha from how magenta a pixel is: min(R, B) - G. Unmix the key colour from edges."""
    p = np.asarray(img).astype(np.float32) / 255.0
    r, g, b = p[..., 0], p[..., 1], p[..., 2]
    spill = np.minimum(r, b) - g
    a = 1.0 - np.clip((spill - 0.10) / 0.80, 0.0, 1.0)
    key = np.array([1.0, 0.0, 1.0], dtype=np.float32)
    safe = np.maximum(a, 1e-3)[..., None]
    fg = np.clip((p - (1.0 - a)[..., None] * key) / safe, 0.0, 1.0)
    fg[a < 0.02] = 0.0
    rgba = np.dstack([fg, a]) * 255.0
    return Image.fromarray(rgba.round().astype(np.uint8), "RGBA")

def trim(img, pad=2):
    box = img.getchannel("A").point(lambda v: 255 if v > 6 else 0).getbbox()
    if not box: return img
    l, t, r, b = box
    return img.crop((max(0, l - pad), max(0, t - pad), min(img.width, r + pad), min(img.height, b + pad)))

def save(img, name):
    img.save(OUT / f"{name}.webp", "WEBP", quality=88, method=6)
    img.save(OUT / f"{name}.png")          # lossless copy for review / future edits
    print(f"  {name}: {img.width}x{img.height}")

def main(urls_path):
    urls = {int(k): v for k, v in json.load(open(urls_path)).items()}
    tiles = {}
    for n, (name, pw, ph) in PAGES.items():
        if n not in urls:
            print(f"  (missing page {n}: {name})"); continue
        img = key_magenta(fetch(urls[n]))
        tiles[name] = (img, img.width / pw)

    for name in ["peacock", "diya", "gopuram", "ganesha", "corner-left", "corner-right"]:
        if name in tiles: save(trim(tiles[name][0]), name)

    if "couple-a" in tiles and "couple-b" in tiles:          # halves overlap by one page pixel
        (a, s), (b, _) = tiles["couple-a"], tiles["couple-b"]
        c = Image.new("RGBA", (a.width, round(811 * s)), (0, 0, 0, 0))
        c.alpha_composite(b, (0, round(405 * s)))
        c.alpha_composite(a, (0, 0))
        save(trim(c), "couple")

    if all(f"toranam-{i}" in tiles for i in (1, 2, 3)):       # three 479px slices of one garland
        s = tiles["toranam-1"][1]
        t = Image.new("RGBA", (round(1437 * s), tiles["toranam-1"][0].height), (0, 0, 0, 0))
        for i in (1, 2, 3):
            t.alpha_composite(tiles[f"toranam-{i}"][0], (round(479 * (i - 1) * s), 0))
        save(trim(t), "toranam")

if __name__ == "__main__":
    main(sys.argv[1])
