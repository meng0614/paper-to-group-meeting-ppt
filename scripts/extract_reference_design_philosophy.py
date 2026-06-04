#!/usr/bin/env python
from __future__ import annotations

import argparse
import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path
from zipfile import ZipFile


EMU_W, EMU_H = 12192000, 6858000


def local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def shape_area(el: ET.Element) -> int:
    ext = None
    for child in el.iter():
        if local(child.tag) == "ext" and "cx" in child.attrib and "cy" in child.attrib:
            ext = child
            break
    if ext is None:
        return 0
    return int(ext.attrib.get("cx", 0)) * int(ext.attrib.get("cy", 0))


def text_len(el: ET.Element) -> int:
    total = 0
    for child in el.iter():
        if local(child.tag) == "t" and child.text:
            total += len(child.text.strip())
    return total


def max_font_size(el: ET.Element) -> float:
    values = []
    for child in el.iter():
        if local(child.tag) == "rPr" and "sz" in child.attrib:
            try:
                values.append(int(child.attrib["sz"]) / 100)
            except ValueError:
                pass
    return max(values) if values else 0.0


def inspect_slide(xml_text: str, idx: int) -> dict:
    root = ET.fromstring(xml_text)
    pic_areas = []
    shape_areas = []
    text_chars = 0
    text_boxes = 0
    text_areas = []
    max_font = 0.0
    for el in root.iter():
        name = local(el.tag)
        if name == "pic":
            pic_areas.append(shape_area(el))
        elif name == "sp":
            area = shape_area(el)
            chars = text_len(el)
            if chars:
                text_chars += chars
                text_boxes += 1
                text_areas.append(area)
                max_font = max(max_font, max_font_size(el))
            if area:
                shape_areas.append(area)
    max_visual = max(pic_areas + shape_areas + [0])
    picture_area = sum(pic_areas)
    text_area = sum(text_areas)
    occupied = min(sum(shape_areas) + sum(pic_areas), EMU_W * EMU_H)
    return {
        "slide": idx,
        "picture_count": len(pic_areas),
        "text_box_count": text_boxes,
        "text_chars": text_chars,
        "picture_area_ratio": round(picture_area / (EMU_W * EMU_H), 3),
        "text_area_ratio": round(text_area / (EMU_W * EMU_H), 3),
        "max_font_size": round(max_font, 1),
        "largest_visual_area_ratio": round(max_visual / (EMU_W * EMU_H), 3),
        "estimated_whitespace_ratio": round(1 - occupied / (EMU_W * EMU_H), 3),
    }


def extract(path: Path) -> dict:
    with ZipFile(path) as zf:
        slide_names = sorted(
            [n for n in zf.namelist() if re.match(r"ppt/slides/slide\d+\.xml$", n)],
            key=lambda n: int(re.search(r"slide(\d+)\.xml", n).group(1)),
        )
        slides = [inspect_slide(zf.read(name).decode("utf-8", errors="ignore"), i + 1) for i, name in enumerate(slide_names)]
    avg_visual = round(sum(s["largest_visual_area_ratio"] for s in slides) / max(1, len(slides)), 3)
    avg_picture = round(sum(s["picture_area_ratio"] for s in slides) / max(1, len(slides)), 3)
    avg_text_area = round(sum(s["text_area_ratio"] for s in slides) / max(1, len(slides)), 3)
    avg_text = round(sum(s["text_chars"] for s in slides) / max(1, len(slides)), 1)
    avg_whitespace = round(sum(s["estimated_whitespace_ratio"] for s in slides) / max(1, len(slides)), 3)
    return {
        "reference_pptx": str(path),
        "policy": "Learn design philosophy only. Do not copy colors or fonts.",
        "learned_design_philosophy": {
            "one_slide_one_message": True,
            "visual_first": True,
            "visual_area_min": 0.40,
            "story_order": ["Problem", "Challenge", "Idea", "Method", "Result", "Takeaway"],
            "whitespace_first": True,
            "audience_first": True,
            "learned_patterns": [
                "stable master frame",
                "clear title hierarchy",
                "visual-text zoning",
                "disciplined whitespace",
                "limited color roles",
                "chapter rhythm",
                "technical visual priority",
            ],
            "do_not_copy": ["colors", "fonts", "theme"],
        },
        "reference_metrics": {
            "slide_count": len(slides),
            "average_largest_visual_area_ratio": avg_visual,
            "average_picture_area_ratio": avg_picture,
            "average_text_area_ratio": avg_text_area,
            "average_text_chars": avg_text,
            "average_whitespace_ratio": avg_whitespace,
        },
        "slide_metrics": slides,
        "recommended_generation_policy": {
            "plan_before_content": True,
            "split_overloaded_slides": True,
            "visual_subject_area_ratio": ">= 0.40",
            "max_primary_message_per_slide": 1,
            "story_first_not_paper_order": True,
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Extract design philosophy metrics from a reference PPTX without copying colors or fonts.")
    parser.add_argument("--reference", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    data = extract(args.reference.resolve())
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(args.out)


if __name__ == "__main__":
    main()
