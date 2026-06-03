#!/usr/bin/env python
from __future__ import annotations

import argparse
import json
from copy import deepcopy
from pathlib import Path
from zipfile import ZipFile

from PIL import Image


MIN_BODY_SIZE = 15
MIN_TITLE_SIZE = 24
MAX_BULLETS = {
    "cover": 3,
    "background": 2,
    "problem": 2,
    "method": 2,
    "algorithm": 2,
    "experiment": 2,
    "result": 2,
    "figure": 3,
    "closing": 3,
    "content": 3,
}


def text_len(value) -> int:
    return len(str(value or "").strip())


def max_bullets(slide: dict) -> int:
    return MAX_BULLETS.get(slide.get("kind", "content"), 3)


def has_visual(slide: dict) -> bool:
    return bool(slide.get("image") or slide.get("visual") or slide.get("table"))


def visual_count(slide: dict) -> int:
    count = 0
    if slide.get("image"):
        count += 1
    if slide.get("visual"):
        count += 1
    if slide.get("table"):
        count += 1
    return count


def validate_pptx_structure(pptx: Path) -> dict:
    with ZipFile(pptx) as zf:
        bad = zf.testzip()
        names = zf.namelist()
        return {
            "zip_error": bad,
            "slide_xml_count": len([n for n in names if n.startswith("ppt/slides/slide") and n.endswith(".xml")]),
            "media_count": len([n for n in names if n.startswith("ppt/media/")]),
        }


def validate_slide(project: Path, slide: dict, idx: int, style: dict) -> dict:
    issues: list[dict] = []
    kind = slide.get("kind", "content")
    bullets = slide.get("bullets", []) or []
    body_size = int(style.get("body_size", 19))
    title_size = int(style.get("title_size", 30))

    if title_size < MIN_TITLE_SIZE:
        issues.append({"type": "Font Readability", "severity": "fail", "detail": f"Title font is too small: {title_size} pt."})
    if body_size < MIN_BODY_SIZE:
        issues.append({"type": "Font Readability", "severity": "fail", "detail": f"Body font is too small: {body_size} pt."})
    if len(bullets) > max_bullets(slide):
        issues.append({"type": "Content Overload", "severity": "fail", "detail": f"{len(bullets)} bullets exceed capacity {max_bullets(slide)}."})
    if any(text_len(b) > 80 for b in bullets):
        issues.append({"type": "Text Overflow", "severity": "fail", "detail": "At least one bullet is longer than 80 characters."})
    if text_len(slide.get("title")) > 72:
        issues.append({"type": "Text Overflow", "severity": "warn", "detail": "Title may overflow the title bar."})
    if kind in {"background", "problem", "method", "algorithm", "experiment", "result"} and not has_visual(slide):
        issues.append({"type": "Object Collision", "severity": "fail", "detail": "No visual center; text will dominate the slide."})
    if visual_count(slide) > 1:
        issues.append({"type": "Image Overlap", "severity": "fail", "detail": "Multiple visual centers are requested on one slide."})
    if slide.get("image"):
        img = project / slide["image"]
        if not img.exists():
            issues.append({"type": "Image Overflow", "severity": "fail", "detail": f"Image file not found: {slide['image']}."})
        else:
            try:
                w, h = Image.open(img).size
                if w < 300 or h < 200:
                    issues.append({"type": "Image Overflow", "severity": "warn", "detail": f"Image is small: {w}x{h}."})
            except Exception as exc:
                issues.append({"type": "Image Overflow", "severity": "fail", "detail": f"Cannot open image: {exc}."})
    if slide.get("visual", {}).get("type") == "result_bar" and len(slide.get("visual", {}).get("items", []) or []) > 4:
        issues.append({"type": "Chart Overflow", "severity": "fail", "detail": "Result chart has more than 4 bars."})

    return {
        "slide": idx,
        "title": slide.get("title", ""),
        "status": "FAIL" if any(i["severity"] == "fail" for i in issues) else "PASS",
        "checks": {
            "Text Overflow": not any(i["type"] == "Text Overflow" and i["severity"] == "fail" for i in issues),
            "Text Overlap": len(bullets) <= max_bullets(slide),
            "Image Overlap": visual_count(slide) <= 1,
            "Chart Overflow": not any(i["type"] == "Chart Overflow" and i["severity"] == "fail" for i in issues),
            "Object Collision": has_visual(slide) or kind in {"cover", "section", "closing"},
            "Font Readability": body_size >= MIN_BODY_SIZE and title_size >= MIN_TITLE_SIZE,
            "Content Overload": len(bullets) <= max_bullets(slide),
        },
        "issues": issues,
    }


def validate(project: Path, spec: dict, pptx: Path | None = None) -> dict:
    style = spec.get("style", {}) or {}
    slide_reports = [validate_slide(project, slide, idx + 1, style) for idx, slide in enumerate(spec.get("slides", []))]
    pptx_report = validate_pptx_structure(pptx) if pptx and pptx.exists() else {}
    passed = all(r["status"] == "PASS" for r in slide_reports) and not pptx_report.get("zip_error")
    return {
        "status": "PASS" if passed else "FAIL",
        "pptx": pptx_report,
        "slides": slide_reports,
        "summary": {
            "text_overflow": all(r["checks"]["Text Overflow"] for r in slide_reports),
            "text_overlap": all(r["checks"]["Text Overlap"] for r in slide_reports),
            "image_overlap": all(r["checks"]["Image Overlap"] for r in slide_reports),
            "chart_overflow": all(r["checks"]["Chart Overflow"] for r in slide_reports),
            "object_collision": all(r["checks"]["Object Collision"] for r in slide_reports),
            "font_readability": all(r["checks"]["Font Readability"] for r in slide_reports),
            "content_overload": all(r["checks"]["Content Overload"] for r in slide_reports),
        },
    }


def fix_spec(spec: dict) -> dict:
    new = deepcopy(spec)
    style = new.setdefault("style", {})
    style["title_size"] = max(MIN_TITLE_SIZE, int(style.get("title_size", 30)))
    style["body_size"] = max(MIN_BODY_SIZE, int(style.get("body_size", 19)))
    fixed_slides: list[dict] = []
    for slide in new.get("slides", []):
        bullets = slide.get("bullets", []) or []
        limit = max_bullets(slide)
        if len(bullets) <= limit and all(text_len(b) <= 80 for b in bullets):
            if not has_visual(slide) and slide.get("kind") not in {"cover", "section", "closing"}:
                slide["visual"] = {"type": "concept", "headline": slide.get("page_goal") or slide.get("title", "")}
            fixed_slides.append(slide)
            continue

        first = deepcopy(slide)
        first["bullets"] = [str(b)[:80] for b in bullets[:limit]]
        fixed_slides.append(first)
        remaining = bullets[limit:]
        while remaining:
            extra = deepcopy(slide)
            extra["title"] = f"{slide.get('title', 'Slide')}: continued"
            extra["page_goal"] = "Continue the same idea on a separate slide to preserve readability."
            extra["visual"] = {"type": "concept", "headline": extra["page_goal"]}
            extra["image"] = None
            extra.pop("table", None)
            extra["bullets"] = [str(b)[:80] for b in remaining[:limit]]
            fixed_slides.append(extra)
            remaining = remaining[limit:]
    new["slides"] = fixed_slides
    return new


def write_report(path: Path, report: dict) -> None:
    lines = ["# Layout Check Report\n\n", f"Overall status: {report['status']}\n\n"]
    lines.append("## Required Checks\n\n")
    labels = {
        "text_overflow": "Text Overflow",
        "text_overlap": "Text Overlap",
        "image_overlap": "Image Overlap",
        "chart_overflow": "Chart Overflow",
        "object_collision": "Object Collision",
        "font_readability": "Font Readability",
        "content_overload": "Content Overload",
    }
    for key, label in labels.items():
        lines.append(f"- {label}: {'PASS' if report['summary'][key] else 'FAIL'}\n")
    lines.append("\n## Slide Details\n\n")
    for slide in report["slides"]:
        lines.append(f"### Slide {slide['slide']}: {slide['title']}\n\n")
        lines.append(f"- Status: {slide['status']}\n")
        for key, ok in slide["checks"].items():
            lines.append(f"- {key}: {'PASS' if ok else 'FAIL'}\n")
        for issue in slide["issues"]:
            lines.append(f"- Issue: [{issue['severity']}] {issue['type']} - {issue['detail']}\n")
        lines.append("\n")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate slide layout capacity before final output.")
    parser.add_argument("--project", type=Path, required=True)
    parser.add_argument("--spec", type=Path, required=True)
    parser.add_argument("--pptx", type=Path)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--json-report", type=Path)
    parser.add_argument("--fix-out", type=Path)
    args = parser.parse_args()
    spec = json.loads(args.spec.read_text(encoding="utf-8"))
    report = validate(args.project.resolve(), spec, args.pptx.resolve() if args.pptx else None)
    write_report(args.report, report)
    if args.json_report:
        args.json_report.parent.mkdir(parents=True, exist_ok=True)
        args.json_report.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    if args.fix_out and report["status"] != "PASS":
        fixed = fix_spec(spec)
        args.fix_out.parent.mkdir(parents=True, exist_ok=True)
        args.fix_out.write_text(json.dumps(fixed, ensure_ascii=False, indent=2), encoding="utf-8")
    print(report["status"])


if __name__ == "__main__":
    main()
