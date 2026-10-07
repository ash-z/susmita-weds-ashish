"""Depth maps for the photographs, so they can shift with the light (nearer things more than farther ones).

    python3 photos_depth.py MODEL.onnx      # -> photos/out/<name>-depth.webp (400x500, grey: lighter is nearer)

MODEL is Depth Anything V2 small as ONNX (depth_anything_v2_vits.onnx, about 100 MB, from the releases of
github.com/fabio-sim/Depth-Anything-ONNX); it is not kept in the repository. Needs onnxruntime, numpy, Pillow.
Run after photos_process.py; the maps are committed, so the build does not need the model.

The map is widened a little around nearer things (a max filter), so that when the photo shifts, the edge of a
person carries a sliver of its own colour rather than tearing into the background behind it.
"""
import sys, pathlib
import numpy as np
import onnxruntime as ort
from PIL import Image, ImageFilter

HERE = pathlib.Path(__file__).resolve().parent
OUT = HERE / "photos" / "out"
MEAN, STD = np.array([0.485, 0.456, 0.406]), np.array([0.229, 0.224, 0.225])

def main(model):
    s = ort.InferenceSession(model)
    name = s.get_inputs()[0].name
    for f in sorted(OUT.glob("*.webp")):
        if f.stem.endswith("-depth"):
            continue
        im = Image.open(f).convert("RGB")
        x = (np.asarray(im.resize((518, 518), Image.BICUBIC), dtype=np.float32) / 255 - MEAN) / STD
        d = s.run(None, {name: x.transpose(2, 0, 1)[None].astype(np.float32)})[0][0]
        lo, hi = np.percentile(d, 1), np.percentile(d, 99)
        d = np.clip((d - lo) / (hi - lo + 1e-6), 0, 1)
        m = Image.fromarray((d * 255).astype(np.uint8)).resize((400, 500), Image.BICUBIC)
        m = m.filter(ImageFilter.MaxFilter(5)).filter(ImageFilter.GaussianBlur(1.5))
        out = OUT / f"{f.stem}-depth.webp"
        m.save(out, "WEBP", quality=85, method=6)
        print(f"  {out.name}: {out.stat().st_size // 1024} KB")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    main(sys.argv[1])
