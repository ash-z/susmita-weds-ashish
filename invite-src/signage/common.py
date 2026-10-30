"""Shared by the signs: Google Fonts subsets cached in fonts/, and the page geometry render.mjs expects."""
import base64, hashlib, pathlib, re, urllib.parse, urllib.request

HERE = pathlib.Path(__file__).resolve().parent
FONTS = HERE / "fonts"; FONTS.mkdir(exist_ok=True)
OUT = HERE / "out"; OUT.mkdir(exist_ok=True)
W, H = 2400, 3600                          # CSS px: 100 per inch (2 x 3 ft); rendered at 1.5x (150 dpi) and as a print PDF
BLEED = 20                                 # 0.2 in (5 mm) of background past the trim on every side, for the printer

def font(family, weight, text):
    """@font-face for a subset of `family` covering `text` (fetched once, then cached in fonts/)"""
    key = hashlib.sha1(f"{family}|{weight}|{text}".encode()).hexdigest()[:10]
    f = FONTS / f"{family.replace(' ', '')}-{weight}-{key}.woff2"
    if not f.exists():
        url = f"https://fonts.googleapis.com/css2?family={family.replace(' ', '+')}:wght@{weight}&text={urllib.parse.quote(text)}"
        css = urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 Chrome/120"})).read().decode()
        f.write_bytes(urllib.request.urlopen(re.search(r"src: url\((https://[^)]+)\)", css).group(1)).read())
    return (f"@font-face{{font-family:'{family}';font-weight:{weight};"
            f"src:url(data:font/woff2;base64,{base64.b64encode(f.read_bytes()).decode()}) format('woff2')}}")
