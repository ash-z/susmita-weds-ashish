"""Generate a fake manga PDF (panels, figures, speed lines) for testing the pipeline."""

import math
import random
import sys

from PIL import Image, ImageDraw


def page(seed: int, n_rows: int) -> Image.Image:
    rnd = random.Random(seed)
    W, H = 1240, 1754
    img = Image.new("RGB", (W, H), "white")
    d = ImageDraw.Draw(img)
    m, g = 70, 28
    row_h = (H - 2 * m - g * (n_rows - 1)) / n_rows
    for r in range(n_rows):
        y0 = m + r * (row_h + g)
        cols = rnd.choice([1, 2, 2, 3])
        col_w = (W - 2 * m - g * (cols - 1)) / cols
        for c in range(cols):
            x0 = m + c * (col_w + g)
            box = (x0, y0, x0 + col_w, y0 + row_h)
            d.rectangle(box, outline="black", width=6)
            cx, cy = (box[0] + box[2]) / 2, (box[1] + box[3]) / 2
            if rnd.random() < 0.5:  # speed lines
                for k in range(40):
                    a = rnd.uniform(0, 2 * math.pi)
                    rr = min(col_w, row_h) / 2
                    d.line((cx + math.cos(a) * rr * 0.3, cy + math.sin(a) * rr * 0.3,
                            cx + math.cos(a) * rr, cy + math.sin(a) * rr), fill="black", width=2)
            s = min(col_w, row_h) * 0.18
            d.ellipse((cx - s, cy - s * 1.6, cx + s, cy + s * 0.4), outline="black", width=5)
            d.rectangle((cx - s * 1.2, cy + s * 0.5, cx + s * 1.2, box[3] - 8), fill=(40, 40, 40))
            d.ellipse((box[0] + 20, box[1] + 20, box[0] + 20 + s * 2.2, box[1] + 20 + s * 1.2),
                      outline="black", fill="white", width=3)
    return img


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else "sample_manga.pdf"
    pages = [page(i, [3, 2, 3, 1, 2][i % 5]) for i in range(6)]
    pages[0].save(out, save_all=True, append_images=pages[1:], resolution=150)
    print(out)
