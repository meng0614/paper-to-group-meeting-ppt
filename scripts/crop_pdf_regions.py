#!/usr/bin/env python
import argparse
import json
from pathlib import Path
from PIL import Image


def crop_region(page_path: Path, box, out_path: Path) -> None:
    im = Image.open(page_path).convert("RGB")
    w, h = im.size
    if all(isinstance(v, float) and 0 <= v <= 1 for v in box):
        x1, y1, x2, y2 = [int(v * (w if i % 2 == 0 else h)) for i, v in enumerate(box)]
    else:
        x1, y1, x2, y2 = [int(v) for v in box]
    out_path.parent.mkdir(parents=True, exist_ok=True)
    im.crop((x1, y1, x2, y2)).save(out_path, "PNG")


def main():
    ap = argparse.ArgumentParser(description="Crop figures/tables/algorithms from rendered PDF page images.")
    ap.add_argument("--pages", type=Path, required=True, help="Directory containing page-01.png etc.")
    ap.add_argument("--spec", type=Path, required=True, help="JSON list of crop objects.")
    ap.add_argument("--out", type=Path, required=True, help="Output figures directory.")
    args = ap.parse_args()

    crops = json.loads(args.spec.read_text(encoding="utf-8"))
    for item in crops:
        page = int(item["page"])
        page_path = args.pages / f"page-{page:02d}.png"
        out_path = args.out / item["file"]
        crop_region(page_path, item["box"], out_path)
        print(out_path)


if __name__ == "__main__":
    main()
