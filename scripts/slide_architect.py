#!/usr/bin/env python
from __future__ import annotations

import argparse
import json
from copy import deepcopy
from pathlib import Path


CAPACITY = {
    "cover": {"bullets": 3, "chars": 160, "steps": 3},
    "background": {"bullets": 2, "chars": 180, "steps": 4},
    "problem": {"bullets": 2, "chars": 170, "steps": 4},
    "method": {"bullets": 2, "chars": 180, "steps": 4},
    "algorithm": {"bullets": 2, "chars": 170, "steps": 4},
    "experiment": {"bullets": 2, "chars": 170, "steps": 4},
    "result": {"bullets": 2, "chars": 170, "steps": 4},
    "figure": {"bullets": 3, "chars": 190, "steps": 4},
    "closing": {"bullets": 3, "chars": 190, "steps": 4},
    "content": {"bullets": 3, "chars": 170, "steps": 4},
}


SPLIT_TITLES = {
    "method": ["Method Overview", "Method Details", "Method Example"],
    "algorithm": ["Algorithm Intuition", "Decision Flow", "Feasibility Check"],
    "experiment": ["Experimental Setup", "Experimental Results", "Experimental Analysis"],
    "result": ["Main Result", "Result Analysis", "So What"],
    "problem": ["Problem Context", "Key Bottleneck", "Why It Matters"],
}


def text_len(value) -> int:
    return len(str(value or "").strip())


def visual_complexity(slide: dict) -> int:
    visual = slide.get("visual") or {}
    if visual.get("type") in {"pipeline", "flow"}:
        return len(visual.get("steps", []) or [])
    if visual.get("type") == "comparison":
        return len(visual.get("left", []) or []) + len(visual.get("right", []) or [])
    if visual.get("type") == "result_bar":
        return len(visual.get("items", []) or [])
    if slide.get("table"):
        rows = slide["table"].get("rows", []) or []
        cols = slide["table"].get("columns", []) or []
        return len(rows) * max(1, len(cols))
    return 1 if slide.get("image") or slide.get("visual") else 0


def capacity_for(slide: dict) -> dict:
    return CAPACITY.get(slide.get("kind", "content"), CAPACITY["content"])


def overloaded(slide: dict) -> bool:
    cap = capacity_for(slide)
    bullets = slide.get("bullets", []) or []
    text_budget = text_len(slide.get("title")) + text_len(slide.get("subtitle")) + text_len(slide.get("content")) + sum(text_len(b) for b in bullets)
    return (
        len(bullets) > cap["bullets"]
        or text_budget > cap["chars"]
        or visual_complexity(slide) > cap["steps"]
        or any(text_len(b) > 70 for b in bullets)
    )


def compact_slide(slide: dict) -> dict:
    new = deepcopy(slide)
    cap = capacity_for(new)
    new.setdefault("page_goal", new.get("title", ""))
    new.setdefault("content", "Minimal text supporting the main visual.")
    new["bullets"] = [str(b).strip() for b in (new.get("bullets", []) or []) if str(b).strip()][: cap["bullets"]]
    visual = new.get("visual") or {}
    if visual.get("type") in {"pipeline", "flow"} and len(visual.get("steps", []) or []) > cap["steps"]:
        visual["steps"] = visual["steps"][: cap["steps"]]
    if visual.get("type") == "comparison":
        visual["left"] = (visual.get("left", []) or [])[:3]
        visual["right"] = (visual.get("right", []) or [])[:3]
    if visual.get("type") == "result_bar":
        visual["items"] = (visual.get("items", []) or [])[:4]
    if visual:
        new["visual"] = visual
    return new


def split_slide(slide: dict) -> list[dict]:
    if not overloaded(slide):
        return [compact_slide(slide)]

    kind = slide.get("kind", "content")
    bullets = slide.get("bullets", []) or []
    visual = slide.get("visual") or {}
    parts: list[dict] = []
    split_names = SPLIT_TITLES.get(kind, ["Overview", "Details", "Takeaway"])

    if visual.get("type") in {"pipeline", "flow"} and len(visual.get("steps", []) or []) > capacity_for(slide)["steps"]:
        steps = visual.get("steps", [])
        mid = max(1, len(steps) // 2)
        for idx, chunk in enumerate([steps[:mid], steps[mid:]]):
            if not chunk:
                continue
            new = deepcopy(slide)
            new["title"] = f"{slide.get('title', kind.title())}: {split_names[min(idx, len(split_names)-1)]}"
            new["page_goal"] = f"{slide.get('page_goal', '')} ({split_names[min(idx, len(split_names)-1)]})"
            new["visual"] = deepcopy(visual)
            new["visual"]["steps"] = chunk
            new["bullets"] = bullets[idx * 2 : idx * 2 + 2]
            parts.append(compact_slide(new))
        return parts

    if len(bullets) > capacity_for(slide)["bullets"]:
        chunk_size = capacity_for(slide)["bullets"]
        for idx in range(0, len(bullets), chunk_size):
            new = deepcopy(slide)
            new["title"] = f"{slide.get('title', kind.title())}: {split_names[min(idx // chunk_size, len(split_names)-1)]}"
            new["page_goal"] = f"{slide.get('page_goal', '')} ({split_names[min(idx // chunk_size, len(split_names)-1)]})"
            new["bullets"] = bullets[idx : idx + chunk_size]
            parts.append(compact_slide(new))
        return parts

    overview = compact_slide(slide)
    overview["content"] = str(overview.get("content", ""))[:120]
    detail = compact_slide(slide)
    detail["title"] = f"{slide.get('title', kind.title())}: Details"
    detail["page_goal"] = "Explain the supporting detail without crowding the overview slide."
    detail["visual"] = {"type": "concept", "headline": detail.get("content", detail.get("title", ""))}
    if kind == "result":
        source_visual = slide.get("visual") or {}
        detail["visual"]["so_what"] = source_visual.get("so_what") or source_visual.get("insight") or "So What: the result supports the paper's core claim."
        detail["visual"]["insight"] = detail["visual"]["so_what"]
    detail["content"] = "Supporting details are moved here to preserve readability."
    detail["bullets"] = bullets[:2]
    return [overview, detail]


def architecture_report(original: list[dict], planned: list[dict]) -> str:
    lines = ["# Slide Architect Report\n\n"]
    lines.append(f"- Original slide count: {len(original)}\n")
    lines.append(f"- Planned slide count: {len(planned)}\n")
    lines.append("- Rule: prefer adding pages over shrinking fonts.\n\n")
    for idx, slide in enumerate(planned, 1):
        cap = capacity_for(slide)
        lines.append(f"## Slide {idx}: {slide.get('title', '')}\n\n")
        lines.append(f"- Kind: {slide.get('kind', 'content')}\n")
        lines.append(f"- Layout: {slide.get('layout', slide.get('style', {}).get('layout', 'auto'))}\n")
        lines.append(f"- Bullet count: {len(slide.get('bullets', []) or [])}/{cap['bullets']}\n")
        lines.append(f"- Visual complexity: {visual_complexity(slide)}/{cap['steps']}\n")
        lines.append(f"- Page Goal: {slide.get('page_goal', '')}\n")
        lines.append(f"- Visual: {(slide.get('visual') or {}).get('type', 'image/table/text')}\n")
        lines.append(f"- Capacity status: {'PASS' if not overloaded(slide) else 'WARN'}\n\n")
    return "".join(lines)


def architect(spec: dict) -> dict:
    new = deepcopy(spec)
    planned: list[dict] = []
    source_key = "sections" if "sections" in spec else "slides"
    for slide in spec.get(source_key, []):
        planned.extend(split_slide(slide))
    new[source_key] = planned
    new.setdefault("planning", {})["slide_architect"] = {
        "original_slide_count": len(spec.get(source_key, [])),
        "planned_slide_count": len(planned),
        "rule": "Prefer splitting pages over shrinking fonts.",
    }
    return new


def main() -> None:
    parser = argparse.ArgumentParser(description="Plan slide count, capacity, and layout before rendering.")
    parser.add_argument("--spec", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    spec = json.loads(args.spec.read_text(encoding="utf-8"))
    planned = architect(spec)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(planned, ensure_ascii=False, indent=2), encoding="utf-8")
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        source_key = "sections" if "sections" in spec else "slides"
        args.report.write_text(architecture_report(spec.get(source_key, []), planned.get(source_key, [])), encoding="utf-8")
    print(args.out)


if __name__ == "__main__":
    main()
