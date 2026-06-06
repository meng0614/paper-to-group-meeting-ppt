#!/usr/bin/env python
from __future__ import annotations

import argparse
import json
from pathlib import Path

from PIL import Image

from generate_academic_presentation import (
    bbox_page,
    find_caption_line,
    infer_search_box,
    postprocess_crop,
    trim_to_visual,
)


def crop_one(pdf: Path, pages_dir: Path, out_dir: Path, item: dict) -> Path:
    page_no = int(item["page"])
    label = str(item["label"])
    page_image = Image.open(pages_dir / f"page-{page_no:02d}.png").convert("RGB")
    bbox = bbox_page(pdf, page_no)
    if bbox:
        caption_line = find_caption_line(bbox, label)
        if caption_line:
            search = infer_search_box(bbox, caption_line, page_image.size)
            crop_box = trim_to_visual(page_image, search[:4], search[4])
        else:
            crop_box = (
                int(page_image.width * 0.08),
                int(page_image.height * 0.08),
                int(page_image.width * 0.92),
                int(page_image.height * 0.65),
            )
    else:
        crop_box = (
            int(page_image.width * 0.08),
            int(page_image.height * 0.08),
            int(page_image.width * 0.92),
            int(page_image.height * 0.65),
        )
    cropped = postprocess_crop(
        page_image.crop(crop_box),
        int(item.get("min_width", 1100)),
        int(item.get("min_height", 430)),
    )
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / item["file"]
    cropped.save(out)
    return out


def main() -> None:
    parser = argparse.ArgumentParser(description="Enhanced caption-aware figure cropper for scholarly PDFs.")
    parser.add_argument("--pdf", type=Path, required=True)
    parser.add_argument("--pages", type=Path, required=True)
    parser.add_argument("--spec", type=Path, required=True, help="JSON list with file/page/label.")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    items = json.loads(args.spec.read_text(encoding="utf-8"))
    for item in items:
        print(crop_one(args.pdf.resolve(), args.pages.resolve(), args.out.resolve(), item))


if __name__ == "__main__":
    main()
