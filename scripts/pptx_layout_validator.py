#!/usr/bin/env python
from __future__ import annotations

import argparse
import json
import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path
from zipfile import ZipFile

EMU_W, EMU_H = 12192000, 6858000


@dataclass
class Shape:
    slide: int
    kind: str
    text: str
    x: int
    y: int
    w: int
    h: int
    max_font: float


def local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def get_box(el: ET.Element) -> tuple[int, int, int, int] | None:
    off = ext = None
    for node in el.iter():
        if local(node.tag) == "off" and "x" in node.attrib and "y" in node.attrib:
            off = node
        elif local(node.tag) == "ext" and "cx" in node.attrib and "cy" in node.attrib:
            ext = node
        if off is not None and ext is not None:
            break
    if off is None or ext is None:
        return None
    return int(off.attrib["x"]), int(off.attrib["y"]), int(ext.attrib["cx"]), int(ext.attrib["cy"])


def get_text(el: ET.Element) -> str:
    return "\n".join((node.text or "").strip() for node in el.iter() if local(node.tag) == "t" and (node.text or "").strip())


def get_max_font(el: ET.Element) -> float:
    values = []
    for node in el.iter():
        if local(node.tag) == "rPr" and "sz" in node.attrib:
            try:
                values.append(int(node.attrib["sz"]) / 100)
            except ValueError:
                pass
    return max(values) if values else 12.0


def estimate_len(text: str) -> float:
    total = 0.0
    for ch in str(text or ""):
        if "\u4e00" <= ch <= "\u9fff":
            total += 1.0
        elif ch.isspace():
            total += 0.35
        else:
            total += 0.58
    return total


def estimated_text_height(shape: Shape) -> int:
    width_factor = max(0.45, shape.w / 3450000)
    capacity = max(10, int(34 * width_factor * (14.5 / max(9, shape.max_font))))
    lines = 0
    for para in shape.text.splitlines() or [""]:
        units = max(1, int(estimate_len(para)))
        lines += max(1, (units + capacity - 1) // capacity)
    return int(lines * shape.max_font * 22000 + 90000)


def decorative_text(shape: Shape) -> bool:
    text = re.sub(r"\s+", " ", shape.text.strip())
    upper = text.upper()
    if not text:
        return True
    if re.fullmatch(r"\d{1,2}", text):
        return True
    if upper in {"BACKGROUND", "PROBLEM", "METHOD", "EXPERIMENT", "RESULTS", "CONCLUSION", "VS", "->"}:
        return True
    if len(text) <= 2:
        return True
    # Small column labels and chart labels are allowed to be tighter than explanatory text.
    if shape.max_font <= 13.5 and estimate_len(text) <= 26:
        return True
    return False


def decorative_shape(shape: Shape) -> bool:
    if shape.kind == "text":
        return decorative_text(shape)
    if shape.kind != "shape":
        return False
    area = shape.w * shape.h
    if area > EMU_W * EMU_H * 0.75:
        return True
    if shape.x <= 1000 and (shape.w <= 180000 or shape.h <= 140000):
        return True
    if shape.y <= 1000 and shape.h <= 140000:
        return True
    return False


def overlap(a: Shape, b: Shape) -> int:
    x1 = max(a.x, b.x)
    y1 = max(a.y, b.y)
    x2 = min(a.x + a.w, b.x + b.w)
    y2 = min(a.y + a.h, b.y + b.h)
    if x2 <= x1 or y2 <= y1:
        return 0
    return (x2 - x1) * (y2 - y1)


def parse_shapes(zf: ZipFile, slide_name: str, slide_idx: int) -> list[Shape]:
    root = ET.fromstring(zf.read(slide_name))
    shapes: list[Shape] = []
    for el in root.iter():
        tag = local(el.tag)
        if tag not in {"sp", "pic"}:
            continue
        box = get_box(el)
        if not box:
            continue
        text = get_text(el)
        kind = "picture" if tag == "pic" else ("text" if text else "shape")
        shapes.append(Shape(slide_idx, kind, text, *box, get_max_font(el)))
    return shapes


def validate(pptx: Path) -> dict:
    issues = []
    with ZipFile(pptx) as zf:
        slides = sorted(
            [n for n in zf.namelist() if re.match(r"ppt/slides/slide\d+\.xml$", n)],
            key=lambda n: int(re.search(r"slide(\d+)\.xml", n).group(1)),
        )
        for idx, name in enumerate(slides, 1):
            shapes = parse_shapes(zf, name, idx)
            text_shapes = [s for s in shapes if s.kind == "text" and s.text]
            content_text_shapes = [s for s in text_shapes if not decorative_text(s)]
            title_shapes = [s for s in content_text_shapes if s.max_font >= 22 and s.y < 1900000]
            title = max(title_shapes, key=lambda s: s.max_font, default=None)
            for s in shapes:
                if s.x < 0 or s.y < 0 or s.x + s.w > EMU_W + 1000 or s.y + s.h > EMU_H + 1000:
                    issues.append({"slide": idx, "type": "Object Overflow", "detail": f"{s.kind} exceeds slide bounds."})
            for s in content_text_shapes:
                needed = estimated_text_height(s)
                if needed > max(s.h * 1.35, s.h + 220000):
                    issues.append({"slide": idx, "type": "Text Overflow", "detail": f"Text box likely too short: needs {needed}, has {s.h}.", "text": s.text[:80]})
            if title:
                for s in shapes:
                    if s is title:
                        continue
                    if decorative_shape(s):
                        continue
                    if s.y < title.y + title.h and overlap(title, s) > 0:
                        issues.append({"slide": idx, "type": "Title Collision", "detail": f"Title overlaps {s.kind}.", "text": title.text[:80]})
                        break
            for i, a in enumerate(content_text_shapes):
                for b in content_text_shapes[i + 1 :]:
                    inter = overlap(a, b)
                    if not inter:
                        continue
                    smaller = max(1, min(a.w * a.h, b.w * b.h))
                    if inter / smaller > 0.08:
                        issues.append({"slide": idx, "type": "Text Overlap", "detail": "Two text boxes overlap.", "text": (a.text[:40] + " / " + b.text[:40])})
                        break
    return {"status": "PASS" if not issues else "NEEDS_REVIEW", "issues": issues}


def write_markdown(path: Path, report: dict) -> None:
    lines = ["# PPTX Layout Check Report\n\n", f"Overall status: {report['status']}\n\n"]
    grouped: dict[int, list[dict]] = {}
    for issue in report["issues"]:
        grouped.setdefault(issue["slide"], []).append(issue)
    if not grouped:
        lines.append("- No title collision, text overlap, object overflow, or likely text overflow found.\n")
    for slide, issues in grouped.items():
        lines.append(f"## Slide {slide}\n\n")
        for issue in issues:
            lines.append(f"- {issue['type']}: {issue['detail']}")
            if issue.get("text"):
                lines.append(f" Text: {issue['text']}")
            lines.append("\n")
        lines.append("\n")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate editable PPTX layout for collisions and text overflow.")
    parser.add_argument("--pptx", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--json-report", type=Path)
    args = parser.parse_args()
    report = validate(args.pptx)
    write_markdown(args.report, report)
    if args.json_report:
        args.json_report.parent.mkdir(parents=True, exist_ok=True)
        args.json_report.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(report["status"])


if __name__ == "__main__":
    main()
