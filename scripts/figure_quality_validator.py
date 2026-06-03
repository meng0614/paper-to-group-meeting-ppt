#!/usr/bin/env python
from __future__ import annotations

import argparse
import json
from pathlib import Path

from PIL import Image, ImageChops, ImageFilter, ImageStat


def content_bbox(im: Image.Image, threshold: int = 246):
    gray = im.convert("L")
    bg = Image.new("L", gray.size, 255)
    diff = ImageChops.difference(gray, bg)
    mask = diff.point(lambda p: 255 if p > (255 - threshold) else 0)
    return mask.getbbox()


def edge_score(gray: Image.Image) -> float:
    edges = gray.filter(ImageFilter.FIND_EDGES)
    stat = ImageStat.Stat(edges)
    return float(stat.mean[0])


def analyze_image(path: Path) -> dict:
    im = Image.open(path).convert("RGB")
    w, h = im.size
    gray = im.convert("L")
    stat = ImageStat.Stat(gray)
    contrast = float(stat.stddev[0])
    bbox = content_bbox(im)
    whitespace_ratio = 0.0
    touched_edges = []
    if bbox:
        x1, y1, x2, y2 = bbox
        content_area = max(1, (x2 - x1) * (y2 - y1))
        whitespace_ratio = 1.0 - content_area / max(1, w * h)
        margin = max(6, int(min(w, h) * 0.012))
        if x1 <= margin:
            touched_edges.append("left")
        if y1 <= margin:
            touched_edges.append("top")
        if x2 >= w - margin:
            touched_edges.append("right")
        if y2 >= h - margin:
            touched_edges.append("bottom")
    sharpness = edge_score(gray)
    issues = []
    if w < 800 or h < 360:
        issues.append("low_resolution")
    if contrast < 18:
        issues.append("low_contrast")
    if sharpness < 4:
        issues.append("possibly_blurry")
    if whitespace_ratio > 0.72:
        issues.append("too_much_whitespace")
    tight_crop = len(touched_edges) >= 2 and whitespace_ratio < 0.12
    one_sided_risk = any(edge in touched_edges for edge in ["left", "right"]) and whitespace_ratio < 0.04
    if tight_crop or one_sided_risk:
        issues.append("possible_incomplete_crop")
    return {
        "file": str(path),
        "width": w,
        "height": h,
        "contrast": round(contrast, 2),
        "sharpness": round(sharpness, 2),
        "whitespace_ratio": round(whitespace_ratio, 3),
        "touched_edges": touched_edges,
        "status": "PASS" if not issues else "NEEDS_REVIEW",
        "issues": issues,
    }


def write_markdown(report_path: Path, rows: list[dict]) -> None:
    report_path.parent.mkdir(parents=True, exist_ok=True)
    total = len(rows)
    failed = [r for r in rows if r["status"] != "PASS"]
    lines = [
        "# Figure Quality Report\n\n",
        f"Status: {'PASS' if not failed else 'NEEDS_REVIEW'}\n\n",
        f"- Figures checked: {total}\n",
        f"- Figures needing review: {len(failed)}\n\n",
        "## Checks\n\n",
        "- low_resolution: crop is too small for projector/PPT use.\n",
        "- possible_incomplete_crop: visual content is very tight against multiple crop edges.\n",
        "- too_much_whitespace: figure should be re-cropped or trimmed.\n",
        "- low_contrast / possibly_blurry: source render DPI or crop quality may be insufficient.\n\n",
        "## Per Figure\n\n",
    ]
    for row in rows:
        rel = Path(row["file"]).name
        issues = ", ".join(row["issues"]) if row["issues"] else "none"
        edges = ",".join(row.get("touched_edges", [])) or "none"
        lines.append(
            f"- {rel}: {row['status']} | {row['width']}x{row['height']} | "
            f"contrast={row['contrast']} | sharpness={row['sharpness']} | "
            f"whitespace={row['whitespace_ratio']} | touched_edges={edges} | issues={issues}\n"
        )
    report_path.write_text("".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Check cropped paper figures for readability and likely crop mistakes.")
    parser.add_argument("--figures", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--json-report", type=Path)
    args = parser.parse_args()

    image_paths = []
    for pattern in ("*.png", "*.jpg", "*.jpeg"):
        image_paths.extend(sorted(args.figures.glob(pattern)))
    rows = [analyze_image(path) for path in image_paths]
    write_markdown(args.report, rows)
    if args.json_report:
        args.json_report.parent.mkdir(parents=True, exist_ok=True)
        args.json_report.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    print("PASS" if all(r["status"] == "PASS" for r in rows) else "NEEDS_REVIEW")


if __name__ == "__main__":
    main()
