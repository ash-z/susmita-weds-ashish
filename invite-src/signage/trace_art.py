"""Trace the gold-mask art (toranam, Ganesha) to vector outlines so it prints crisp at sign size.

    python3 invite-src/signage/trace_art.py           # -> invite-src/signage/vector/{toranam,ganesha}.svg  (needs Pillow, numpy, potracer)

The sign only uses these pieces as a foil mask, i.e. their alpha silhouette, so tracing loses nothing; the PNG sources
are small (the toranam prints at ~65 dpi) and would print with ragged edges. The SVGs are committed, so the sign
itself doesn't need these packages.
"""
import pathlib
import numpy as np, potrace
from PIL import Image

HERE = pathlib.Path(__file__).resolve().parent
UP = 4                                     # trace an upsampled alpha so curves follow the soft edge, not the pixel grid

def trace(name):
    a = Image.open(HERE.parent / "art" / f"{name}.png").getchannel("A")
    w, h = a.size
    big = np.asarray(a.resize((w * UP, h * UP), Image.LANCZOS)) <= 127   # potracer fills the False pixels
    d = []
    for curve in potrace.Bitmap(big).trace(turdsize=8 * UP, alphamax=1.0, opticurve=True, opttolerance=0.2):
        f = lambda p: f"{p.x / UP:.2f} {p.y / UP:.2f}"
        d.append("M" + f(curve.start_point))
        for s in curve.segments:
            d.append(f"L{f(s.c)} L{f(s.end_point)}" if s.is_corner else f"C{f(s.c1)} {f(s.c2)} {f(s.end_point)}")
        d.append("Z")
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}">'
           f'<path fill-rule="evenodd" d="{"".join(d)}"/></svg>')
    (HERE / "vector" / f"{name}.svg").write_text(svg)
    print(name, f"{len(svg) // 1024} KB")

for n in ("toranam", "ganesha"):
    trace(n)
