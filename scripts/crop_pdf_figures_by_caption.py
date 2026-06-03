#!/usr/bin/env python
from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import tempfile
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path

from PIL import Image


@dataclass
class Line:
    text: str
    x1: float
    y1: float
    x2: float
    y2: float


@dataclass
class PageText:
    width: float
    height: float
    lines: list[Line]


def local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def parse_bbox_html(path: Path) -> PageText:
    root = ET.fromstring(path.read_text(encoding="utf-8", errors="ignore"))
    page_el = next(el for el in root.iter() if local_name(el.tag) == "page")
    page = PageText(float(page_el.attrib["width"]), float(page_el.attrib["height"]), [])
    for line_el in page_el.iter():
        if local_name(line_el.tag) != "line":
            continue
        words = [w for w in line_el if local_name(w.tag) == "word"]
        if not words:
            continue
        text = " ".join((w.text or "").strip() for w in words).strip()
        if not text:
            continue
        page.lines.append(
            Line(
                text=text,
                x1=min(float(w.attrib["xMin"]) for w in words),
                y1=min(float(w.attrib["yMin"]) for w in words),
                x2=max(float(w.attrib["xMax"]) for w in words),
                y2=max(float(w.attrib["yMax"]) for w in words),
            )
        )
    return page


def run_pdftotext(pdf: Path, page: int) -> PageText:
    exe = shutil.which("pdftotext")
    if not exe:
        raise RuntimeError("pdftotext not found. Install Poppler/TeX Live, or provide manual clean crop boxes.")
    with tempfile.TemporaryDirectory() as td:
        out = Path(td) / f"page_{page}.html"
        subprocess.run([exe, "-bbox-layout", "-f", str(page), "-l", str(page), str(pdf), str(out)], check=True)
        return parse_bbox_html(out)


def find_caption_line(page: PageText, label: str) -> Line:
    normalized = label.strip().rstrip(".")
    escaped = re.escape(normalized).replace(r"\ ", r"\s+")
    pattern = re.compile(rf"\b{escaped}\.?\b", re.IGNORECASE)
    candidates = [line for line in page.lines if pattern.search(line.text)]
    if not candidates and normalized.lower().startswith("fig"):
        number = re.sub(r"[^0-9A-Za-z.]", "", normalized.split()[-1]).rstrip(".")
        candidates = [
            line
            for line in page.lines
            if re.search(r"\bFig\.?\b", line.text, re.IGNORECASE) and number and number in line.text
        ]
    if not candidates:
        raise ValueError(f"Cannot locate caption label {label!r}")
    # Caption lines are usually smaller text; choose the shortest matching line to avoid body references like "Fig. 2(a)".
    return min(candidates, key=lambda line: (line.y1, len(line.text)))


def infer_column(page: PageText, caption: Line, mode: str) -> tuple[float, float]:
    margin = max(36.0, page.width * 0.07)
    gutter = max(8.0, page.width * 0.015)
    mid = page.width / 2
    center = (caption.x1 + caption.x2) / 2
    if mode == "full":
        return margin, page.width - margin
    if mode == "left":
        return margin, mid - gutter
    if mode == "right":
        return mid + gutter, page.width - margin
    if caption.x2 - caption.x1 > page.width * 0.45:
        return margin, page.width - margin
    return (mid + gutter, page.width - margin) if center >= mid else (margin, mid - gutter)


def find_visual_band(gray: Image.Image, x1: int, y1: int, x2: int, y2: int) -> tuple[int, int, int, int]:
    region = gray.crop((x1, y1, x2, y2))
    w, h = region.size
    pix = region.load()
    rows = []
    for y in range(h):
        dark = sum(1 for x in range(w) if pix[x, y] < 245)
        if dark > max(3, int(w * 0.006)):
            rows.append(y)
    if not rows:
        return x1, y1, x2, y2
    groups = []
    start = prev = rows[0]
    for row in rows[1:]:
        if row - prev > 42:
            groups.append((start, prev))
            start = row
        prev = row
    groups.append((start, prev))
    # Pick the content band closest to the caption and merge nearby subfigure bands.
    sel_start, sel_end = groups[-1]
    for g_start, g_end in reversed(groups[:-1]):
        if sel_start - g_end <= 70:
            sel_start = g_start
        else:
            break
    pad_y = 8
    cy1 = max(0, sel_start - pad_y)
    cy2 = min(h, sel_end + pad_y + 1)
    band = region.crop((0, cy1, w, cy2))
    cols = []
    bpix = band.load()
    bw, bh = band.size
    for x in range(bw):
        dark = sum(1 for y in range(bh) if bpix[x, y] < 245)
        if dark > max(2, int(bh * 0.006)):
            cols.append(x)
    if cols:
        cx1 = max(0, min(cols) - 8)
        cx2 = min(w, max(cols) + 9)
    else:
        cx1, cx2 = 0, w
    return x1 + cx1, y1 + cy1, x1 + cx2, y1 + cy2


def crop_one(pdf: Path, pages_dir: Path, out_dir: Path, item: dict, dpi_hint: int | None = None) -> Path:
    page_no = int(item["page"])
    label = str(item["label"])
    page_text = run_pdftotext(pdf, page_no)
    caption = find_caption_line(page_text, label)
    col_x1, col_x2 = infer_column(page_text, caption, str(item.get("column", "auto")).lower())

    page_img = Image.open(pages_dir / f"page-{page_no:02d}.png").convert("RGB")
    img_w, img_h = page_img.size
    sx = img_w / page_text.width
    sy = img_h / page_text.height
    position = str(item.get("position", "above")).lower()
    header_guard = float(item.get("header_guard", 45.0))
    pad = int(item.get("padding", 8))
    if position == "below":
        search_y1 = int((caption.y2 + 2) * sy)
        search_y2 = int((page_text.height - header_guard) * sy)
    else:
        search_y1 = int(header_guard * sy)
        search_y2 = int((caption.y1 - 2) * sy)
    search_x1 = int(col_x1 * sx)
    search_x2 = int(col_x2 * sx)
    search_y1 = max(0, min(search_y1, img_h - 1))
    search_y2 = max(search_y1 + 1, min(search_y2, img_h))
    search_x1 = max(0, min(search_x1, img_w - 1))
    search_x2 = max(search_x1 + 1, min(search_x2, img_w))

    gray = page_img.convert("L")
    x1, y1, x2, y2 = find_visual_band(gray, search_x1, search_y1, search_x2, search_y2)
    x1 = max(0, x1 - pad)
    y1 = max(0, y1 - pad)
    x2 = min(img_w, x2 + pad)
    y2 = min(img_h, y2 + pad)
    cropped = page_img.crop((x1, y1, x2, y2))
    min_width = int(item.get("min_width", 1000))
    min_height = int(item.get("min_height", 420))
    scale = max(min_width / max(1, cropped.size[0]), min_height / max(1, cropped.size[1]), 1.0)
    if scale > 1.01:
        cropped = cropped.resize((int(cropped.size[0] * scale), int(cropped.size[1] * scale)), Image.Resampling.LANCZOS)
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / item["file"]
    cropped.save(out, "PNG")
    return out


def main() -> None:
    parser = argparse.ArgumentParser(description="Caption-aware clean figure cropper for scholarly PDFs.")
    parser.add_argument("--pdf", type=Path, required=True)
    parser.add_argument("--pages", type=Path, required=True)
    parser.add_argument("--spec", type=Path, required=True, help="JSON list with file/page/label, e.g. label='Fig. 2'.")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    items = json.loads(args.spec.read_text(encoding="utf-8"))
    for item in items:
        print(crop_one(args.pdf, args.pages, args.out, item))


if __name__ == "__main__":
    main()
