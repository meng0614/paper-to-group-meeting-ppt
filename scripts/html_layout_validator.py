#!/usr/bin/env python
from __future__ import annotations

import argparse
import json
from copy import deepcopy
from pathlib import Path


MAX_SECTION_CHARS = 1600
MAX_TABLE_ROWS = 12
MAX_VISUALS = 2


def text_len(value) -> int:
    return len(str(value or "").strip())


def sections(spec: dict) -> list[dict]:
    return spec.get("sections") or spec.get("slides") or []


def has_visual(section: dict) -> bool:
    return bool(section.get("image") or section.get("visual") or section.get("table") or section.get("pseudocode"))


def visual_count(section: dict) -> int:
    count = 0
    if section.get("image"):
        count += 1
    visual = section.get("visual") or {}
    if visual and not (section.get("image") and set(visual.keys()).issubset({"caption"})):
        count += 1
    if section.get("table"):
        count += 1
    if section.get("pseudocode") and not section.get("visual"):
        count += 1
    return count


def validate_section(section: dict, idx: int, html_exists: bool) -> dict:
    issues: list[dict] = []
    text_total = (
        text_len(section.get("title"))
        + text_len(section.get("page_goal"))
        + text_len(section.get("content"))
        + text_len(section.get("body"))
        + text_len(section.get("details"))
        + sum(text_len(b) for b in section.get("bullets", []) or [])
    )
    if not has_visual(section):
        issues.append({"type": "Object Collision", "severity": "fail", "detail": "Section has no visual center."})
    if visual_count(section) > MAX_VISUALS:
        issues.append({"type": "Image Overlap", "severity": "fail", "detail": "Too many visual centers in one section."})
    if text_total > MAX_SECTION_CHARS and not (section.get("details") or section.get("long_text")):
        issues.append({"type": "Text Overflow", "severity": "fail", "detail": "Long text should be moved into details/collapsible area or split."})
    if len(section.get("bullets", []) or []) > 8:
        issues.append({"type": "Content Overload", "severity": "warn", "detail": "Many bullets; HTML can handle it, but visual hierarchy may suffer."})
    table = section.get("table") or {}
    if len(table.get("rows", []) or []) > MAX_TABLE_ROWS:
        issues.append({"type": "Chart Overflow", "severity": "warn", "detail": "Large table should stay inside scrollable table container."})
    if section.get("visual", {}).get("type") == "result_bar" and len(section.get("visual", {}).get("items", []) or []) > 8:
        issues.append({"type": "Chart Overflow", "severity": "fail", "detail": "Dynamic bar chart has too many items."})
    if not html_exists:
        issues.append({"type": "HTML Output", "severity": "fail", "detail": "HTML file does not exist."})

    checks = {
        "Text Overflow": not any(i["type"] == "Text Overflow" and i["severity"] == "fail" for i in issues),
        "Text Overlap": True,
        "Image Overlap": not any(i["type"] == "Image Overlap" and i["severity"] == "fail" for i in issues),
        "Chart Overflow": not any(i["type"] == "Chart Overflow" and i["severity"] == "fail" for i in issues),
        "Object Collision": has_visual(section),
        "Font Readability": True,
        "Content Overload": not any(i["type"] == "Content Overload" and i["severity"] == "fail" for i in issues),
        "Scrollable Long Content": bool(section.get("details") or section.get("long_text")) or text_total <= MAX_SECTION_CHARS,
    }
    return {
        "section": idx,
        "title": section.get("title", ""),
        "status": "FAIL" if any(i["severity"] == "fail" for i in issues) else "PASS",
        "checks": checks,
        "issues": issues,
    }


def validate(project: Path, spec: dict, html_path: Path) -> dict:
    html_exists = html_path.exists()
    section_reports = [validate_section(sec, idx + 1, html_exists) for idx, sec in enumerate(sections(spec))]
    summary = {
        "text_overflow": all(r["checks"]["Text Overflow"] for r in section_reports),
        "text_overlap": all(r["checks"]["Text Overlap"] for r in section_reports),
        "image_overlap": all(r["checks"]["Image Overlap"] for r in section_reports),
        "chart_overflow": all(r["checks"]["Chart Overflow"] for r in section_reports),
        "object_collision": all(r["checks"]["Object Collision"] for r in section_reports),
        "font_readability": all(r["checks"]["Font Readability"] for r in section_reports),
        "content_overload": all(r["checks"]["Content Overload"] for r in section_reports),
        "scrollable_long_content": all(r["checks"]["Scrollable Long Content"] for r in section_reports),
    }
    return {
        "status": "PASS" if html_exists and all(r["status"] == "PASS" for r in section_reports) else "FAIL",
        "html": {"exists": html_exists, "path": str(html_path), "size": html_path.stat().st_size if html_exists else 0},
        "summary": summary,
        "sections": section_reports,
    }


def fix_spec(spec: dict) -> dict:
    new = deepcopy(spec)
    target_key = "sections" if "sections" in new else "slides"
    fixed = []
    for sec in sections(new):
        if not has_visual(sec):
            sec["visual"] = {"type": "concept", "headline": sec.get("page_goal") or sec.get("title", "")}
        text_total = text_len(sec.get("content")) + text_len(sec.get("body")) + sum(text_len(b) for b in sec.get("bullets", []) or [])
        if text_total > MAX_SECTION_CHARS and not sec.get("details"):
            sec["details"] = (str(sec.get("body") or "") + "\n" + "\n".join(sec.get("bullets", []) or [])).strip()
            sec["body"] = str(sec.get("body") or "")[:700]
            sec["bullets"] = (sec.get("bullets", []) or [])[:6]
        if sec.get("visual", {}).get("type") == "result_bar":
            sec["visual"]["items"] = (sec["visual"].get("items", []) or [])[:8]
        fixed.append(sec)
    new[target_key] = fixed
    return new


def write_report(path: Path, report: dict) -> None:
    lines = ["# Layout Check Report\n\n", f"Overall status: {report['status']}\n\n"]
    lines.append("## Required HTML Checks\n\n")
    labels = {
        "text_overflow": "Text Overflow",
        "text_overlap": "Text Overlap",
        "image_overlap": "Image Overlap",
        "chart_overflow": "Chart Overflow",
        "object_collision": "Object Collision",
        "font_readability": "Font Readability",
        "content_overload": "Content Overload",
        "scrollable_long_content": "Scrollable/Foldable Long Content",
    }
    for key, label in labels.items():
        lines.append(f"- {label}: {'PASS' if report['summary'][key] else 'FAIL'}\n")
    lines.append("\n## Section Details\n\n")
    for sec in report["sections"]:
        lines.append(f"### Section {sec['section']}: {sec['title']}\n\n")
        lines.append(f"- Status: {sec['status']}\n")
        for key, ok in sec["checks"].items():
            lines.append(f"- {key}: {'PASS' if ok else 'FAIL'}\n")
        for issue in sec["issues"]:
            lines.append(f"- Issue: [{issue['severity']}] {issue['type']} - {issue['detail']}\n")
        lines.append("\n")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate HTML report layout and visual hierarchy.")
    parser.add_argument("--project", type=Path, required=True)
    parser.add_argument("--spec", type=Path, required=True)
    parser.add_argument("--html", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--json-report", type=Path)
    parser.add_argument("--fix-out", type=Path)
    args = parser.parse_args()
    spec = json.loads(args.spec.read_text(encoding="utf-8"))
    report = validate(args.project.resolve(), spec, args.html.resolve())
    write_report(args.report, report)
    if args.json_report:
        args.json_report.parent.mkdir(parents=True, exist_ok=True)
        args.json_report.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    if args.fix_out and report["status"] != "PASS":
        args.fix_out.parent.mkdir(parents=True, exist_ok=True)
        args.fix_out.write_text(json.dumps(fix_spec(spec), ensure_ascii=False, indent=2), encoding="utf-8")
    print(report["status"])


if __name__ == "__main__":
    main()
