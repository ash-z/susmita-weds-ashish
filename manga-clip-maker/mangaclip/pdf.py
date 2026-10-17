"""PDF loading and page rendering."""

from __future__ import annotations

import base64
import io
from dataclasses import dataclass, field

import pymupdf as fitz
from PIL import Image


@dataclass
class Page:
    number: int  # 1-based
    image: Image.Image  # high-res RGB render used for the video
    _cache: dict = field(default_factory=dict, repr=False)

    def thumbnail(self, long_side: int) -> Image.Image:
        if long_side not in self._cache:
            img = self.image.copy()
            img.thumbnail((long_side, long_side), Image.LANCZOS)
            self._cache[long_side] = img
        return self._cache[long_side]

    def jpeg_b64(self, long_side: int, quality: int = 82) -> str:
        buf = io.BytesIO()
        self.thumbnail(long_side).save(buf, format="JPEG", quality=quality)
        return base64.standard_b64encode(buf.getvalue()).decode("ascii")


def load_pages(path: str, target_height: int = 2400, first: int | None = None,
               last: int | None = None) -> list[Page]:
    """Render PDF pages to RGB images roughly `target_height` pixels tall."""
    doc = fitz.open(path)
    start = (first or 1) - 1
    stop = min(last or doc.page_count, doc.page_count)
    pages = []
    for i in range(start, stop):
        page = doc.load_page(i)
        zoom = target_height / max(page.rect.height, 1)
        pix = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom), alpha=False)
        img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
        pages.append(Page(number=i + 1, image=img))
    doc.close()
    return pages
