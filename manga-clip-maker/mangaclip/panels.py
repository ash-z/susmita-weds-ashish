"""Panel detection by recursive XY-cut along white gutters.

Works well for classic rectangular manga layouts. Irregular layouts fall back
to the whole page (or to boxes supplied by Claude).
"""

from __future__ import annotations

import numpy as np
from PIL import Image

Box = tuple[float, float, float, float]  # normalized x0, y0, x1, y1


def _gutters(profile: np.ndarray, min_gap: int) -> list[tuple[int, int]]:
    """Return (start, end) runs where `profile` is True and the run is >= min_gap."""
    runs, start = [], None
    for i, v in enumerate(profile):
        if v and start is None:
            start = i
        elif not v and start is not None:
            if i - start >= min_gap:
                runs.append((start, i))
            start = None
    if start is not None and len(profile) - start >= min_gap:
        runs.append((start, len(profile)))
    return runs


def _split(ink: np.ndarray, x0: int, y0: int, x1: int, y1: int, depth: int,
           out: list[tuple[int, int, int, int]], min_size: int) -> None:
    region = ink[y0:y1, x0:x1]
    if region.size == 0:
        return
    h, w = region.shape
    # Trim blank borders.
    rows = region.mean(axis=1) > 0.004
    cols = region.mean(axis=0) > 0.004
    if not rows.any() or not cols.any():
        return
    ry = np.flatnonzero(rows)
    rx = np.flatnonzero(cols)
    y0, y1 = y0 + ry[0], y0 + ry[-1] + 1
    x0, x1 = x0 + rx[0], x0 + rx[-1] + 1
    region = ink[y0:y1, x0:x1]
    h, w = region.shape
    if depth > 6 or h < min_size or w < min_size:
        out.append((x0, y0, x1, y1))
        return

    gap = max(3, min(h, w) // 80)
    # Prefer horizontal cuts first (manga rows), then vertical.
    for axis in (1, 0):
        prof = region.mean(axis=axis) < 0.004
        runs = [r for r in _gutters(prof, gap)
                if r[0] > 0 and r[1] < (h if axis == 1 else w)]
        if not runs:
            continue
        cuts = [0] + [(a + b) // 2 for a, b in runs] + [h if axis == 1 else w]
        pieces = [(cuts[i], cuts[i + 1]) for i in range(len(cuts) - 1)]
        if axis == 1:
            for a, b in pieces:
                _split(ink, x0, y0 + a, x1, y0 + b, depth + 1, out, min_size)
        else:
            for a, b in pieces:
                _split(ink, x0 + a, y0, x0 + b, y1, depth + 1, out, min_size)
        return
    out.append((x0, y0, x1, y1))


def detect_panels(img: Image.Image, right_to_left: bool = True) -> list[Box]:
    """Detect panels and return normalized boxes in reading order."""
    small = img.convert("L")
    small.thumbnail((800, 800))
    arr = np.asarray(small, dtype=np.float32) / 255.0
    ink = (arr < 0.88).astype(np.float32)
    h, w = ink.shape
    found: list[tuple[int, int, int, int]] = []
    _split(ink, 0, 0, w, h, 0, found, min_size=max(40, min(h, w) // 8))
    area = w * h
    boxes = [b for b in found if (b[2] - b[0]) * (b[3] - b[1]) > area * 0.02]
    if not boxes:
        return [(0.0, 0.0, 1.0, 1.0)]
    norm = [(b[0] / w, b[1] / h, b[2] / w, b[3] / h) for b in boxes]
    return sort_reading_order(norm, right_to_left)


def sort_reading_order(boxes: list[Box], right_to_left: bool = True) -> list[Box]:
    """Group boxes into rows by vertical overlap, then order within each row."""
    rows: list[list[Box]] = []
    for b in sorted(boxes, key=lambda b: b[1]):
        for row in rows:
            ry0 = min(r[1] for r in row)
            ry1 = max(r[3] for r in row)
            overlap = min(ry1, b[3]) - max(ry0, b[1])
            if overlap > 0.5 * min(b[3] - b[1], ry1 - ry0):
                row.append(b)
                break
        else:
            rows.append([b])
    ordered = []
    for row in rows:
        ordered.extend(sorted(row, key=lambda b: -b[2] if right_to_left else b[0]))
    return ordered


def iou(a: Box, b: Box) -> float:
    ix = max(0.0, min(a[2], b[2]) - max(a[0], b[0]))
    iy = max(0.0, min(a[3], b[3]) - max(a[1], b[1]))
    inter = ix * iy
    union = (a[2] - a[0]) * (a[3] - a[1]) + (b[2] - b[0]) * (b[3] - b[1]) - inter
    return inter / union if union > 0 else 0.0


def snap(box: Box, detected: list[Box], threshold: float = 0.5) -> Box:
    """Snap a roughly-placed box onto the best matching detected panel."""
    best = max(detected, key=lambda d: iou(box, d), default=None)
    if best is not None and iou(box, best) >= threshold:
        return best
    return box


def visual_stats(img: Image.Image) -> dict:
    """Cheap visual features used by the offline interest heuristic."""
    g = img.convert("L")
    g.thumbnail((600, 600))
    a = np.asarray(g, dtype=np.float32) / 255.0
    gx = np.abs(np.diff(a, axis=1)).mean()
    gy = np.abs(np.diff(a, axis=0)).mean()
    return {"ink": float((a < 0.5).mean()), "edges": float(gx + gy)}
