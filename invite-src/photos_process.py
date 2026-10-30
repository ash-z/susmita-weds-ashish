"""Crop the couple's photographs for the photo deck (4:5 cards).

    python3 photos_process.py            # -> photos/out/*.webp (800x1000)

Crops are chosen by eye per photo (x, y, width in source pixels; height is
width * 5/4) to frame the faces and leave out relatives at the edges and the
screenshot bars at the bottom.
"""
import pathlib
from PIL import Image, ImageOps

HERE = pathlib.Path(__file__).resolve().parent
SRC, OUT = HERE / "photos", HERE / "photos" / "out"
OUT.mkdir(exist_ok=True)

# deck order: name, source file (by timestamp), crop x, y, width
DECK = [
    ("together-laughing", "07-59-19-491", 0,   317, 1161),
    ("susmita",           "07-59-12-956", 100, 330, 1000),
    ("ashish",            "07-59-05-226", 150, 200,  960),
    ("together-portrait", "07-59-16-387", 0,   200, 1200),
    ("together-ring",     "07-59-27-571", 0,    60, 1200),
    # not a deck card: the opening screen's arch window, cropped close on the two of them
    ("cover",             "07-59-16-387", 140, 100,  960),
]

def src(stamp):
    return next(SRC.glob(f"*{stamp}*.jpg"))

def main():
    for name, stamp, x, y, w in DECK:
        im = ImageOps.exif_transpose(Image.open(src(stamp))).convert("RGB")
        h = round(w * 5 / 4)
        assert x + w <= im.width and y + h <= im.height, (name, im.size, (x, y, w, h))
        card = im.crop((x, y, x + w, y + h)).resize((800, 1000), Image.LANCZOS)
        card.save(OUT / f"{name}.webp", "WEBP", quality=80, method=6)
        print(f"  {name}: {(OUT / f'{name}.webp').stat().st_size // 1024} KB")

if __name__ == "__main__":
    main()
