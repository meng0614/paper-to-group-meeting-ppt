#!/usr/bin/env python
from __future__ import annotations

import argparse
import json
import re
from copy import deepcopy
from pathlib import Path


CAPACITY = {
    "cover": {"bullets": 3, "chars": 360, "steps": 3},
    "background": {"bullets": 2, "chars": 360, "steps": 4},
    "problem": {"bullets": 2, "chars": 340, "steps": 4},
    "motivation": {"bullets": 2, "chars": 340, "steps": 4},
    "method": {"bullets": 2, "chars": 360, "steps": 4},
    "algorithm": {"bullets": 2, "chars": 340, "steps": 4},
    "experiment": {"bullets": 2, "chars": 340, "steps": 4},
    "result": {"bullets": 2, "chars": 340, "steps": 4},
    "figure": {"bullets": 3, "chars": 400, "steps": 4},
    "closing": {"bullets": 3, "chars": 360, "steps": 4},
    "content": {"bullets": 3, "chars": 340, "steps": 4},
}

STORY_ORDER = ["Problem", "Challenge", "Idea", "Method", "Result", "Takeaway"]

STORY_BY_KIND = {
    "cover": "Problem",
    "background": "Problem",
    "problem": "Problem",
    "motivation": "Challenge",
    "challenge": "Challenge",
    "idea": "Idea",
    "method": "Method",
    "algorithm": "Method",
    "figure": "Method",
    "experiment": "Result",
    "result": "Result",
    "results": "Result",
    "closing": "Takeaway",
    "conclusion": "Takeaway",
}


SPLIT_TITLES = {
    "method": ["Method Overview", "Method Details", "Method Example"],
    "algorithm": ["Algorithm Intuition", "Decision Flow", "Feasibility Check"],
    "experiment": ["Experimental Setup", "Experimental Results", "Experimental Analysis"],
    "result": ["Main Result", "Result Analysis", "So What"],
    "problem": ["Problem Context", "Key Bottleneck", "Why It Matters"],
}


DETAIL_TITLES_ZH = {
    "cover": "论文一句话：研究对象、核心转向、验证逻辑",
    "background": "背景细节：需求如何变成技术瓶颈",
    "problem": "瓶颈细节：旧方法为什么不够",
    "motivation": "动机细节：旧范式如何转向本文动作",
    "method": "方法细节：核心机制和输入输出",
    "algorithm": "机制细节：决策流程如何成立",
    "experiment": "实验细节：设置、基线、指标",
    "result": "结果细节：证据如何支撑 claim",
    "closing": "总结细节：贡献、创新与边界",
    "content": "补充说明：支撑本页核心观点",
}

DETAIL_TITLES_EN = {
    "cover": "Paper in One Sentence: Object, Move, Evidence",
    "background": "Background Detail: From Demand to Bottleneck",
    "problem": "Bottleneck Detail: Why Existing Work Is Insufficient",
    "motivation": "Motivation Detail: From Old Paradigm to Paper Move",
    "method": "Method Detail: Mechanism, Inputs, Outputs",
    "algorithm": "Mechanism Detail: Why the Decision Flow Holds",
    "experiment": "Experiment Detail: Setup, Baselines, Metrics",
    "result": "Result Detail: Evidence to Claim",
    "closing": "Takeaway Detail: Contribution, Novelty, Boundary",
    "content": "Supporting Detail: Evidence Behind the Message",
}


def text_len(value) -> int:
    return len(str(value or "").strip())


def has_cjk(value: str) -> bool:
    return bool(re.search(r"[\u4e00-\u9fff]", str(value or "")))


def detail_title(slide: dict) -> str:
    kind = str(slide.get("kind", "content")).lower()
    titles = DETAIL_TITLES_ZH if has_cjk(slide.get("title", "") + slide.get("content", "")) else DETAIL_TITLES_EN
    return titles.get(kind, titles["content"])


def compact_title(value: str, limit: int = 34) -> str:
    text = str(value or "").strip()
    if len(text) <= limit:
        return text
    return text[:limit].rstrip() + "..."


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


def has_visual(slide: dict) -> bool:
    return bool(slide.get("image") or slide.get("visual") or slide.get("table") or slide.get("pseudocode"))


def infer_story_phase(slide: dict) -> str:
    explicit = slide.get("story_phase")
    if explicit:
        normalized = str(explicit).strip().title()
        return normalized if normalized in STORY_ORDER else str(explicit).strip()
    kind = str(slide.get("kind", "content")).lower()
    title = str(slide.get("title", "")).lower()
    if any(token in title for token in ["challenge", "limitation", "bottleneck", "局限", "挑战", "瓶颈"]):
        return "Challenge"
    if any(token in title for token in ["idea", "insight", "key", "核心思想", "关键思想"]):
        return "Idea"
    if any(token in title for token in ["result", "evaluation", "experiment", "结果", "实验"]):
        return "Result"
    if any(token in title for token in ["takeaway", "conclusion", "limitation", "future", "总结", "局限"]):
        return "Takeaway"
    return STORY_BY_KIND.get(kind, "Idea")


def story_sort_key(item: tuple[int, dict]) -> tuple[int, int]:
    idx, slide = item
    kind = str(slide.get("kind", "")).lower()
    if kind == "cover":
        return (-1, idx)
    phase = infer_story_phase(slide)
    return (STORY_ORDER.index(phase) if phase in STORY_ORDER else 2, idx)


def capacity_for(slide: dict) -> dict:
    return CAPACITY.get(slide.get("kind", "content"), CAPACITY["content"])


def overloaded(slide: dict) -> bool:
    cap = capacity_for(slide)
    bullets = slide.get("bullets", []) or []
    text_budget = text_len(slide.get("title")) + text_len(slide.get("subtitle")) + text_len(slide.get("content")) + sum(text_len(b) for b in bullets)
    visual = slide.get("visual") or {}
    visual_limit = 6 if visual.get("type") == "comparison" else cap["steps"]
    return (
        len(bullets) > cap["bullets"]
        or text_budget > cap["chars"]
        or visual_complexity(slide) > visual_limit
        or any(text_len(b) > 70 for b in bullets)
    )


def compact_slide(slide: dict) -> dict:
    new = deepcopy(slide)
    cap = capacity_for(new)
    new["story_phase"] = infer_story_phase(new)
    new.setdefault("one_message", new.get("title") or new.get("page_goal", ""))
    new.setdefault("page_goal", new.get("one_message") or new.get("title", ""))
    new.setdefault("audience_takeaway", new.get("page_goal", ""))
    new.setdefault("visual_area_min", 0.40)
    new.setdefault("design_brief", {
        "principle": "One Slide One Message / Visual First / Whitespace First",
        "visual_subject_area": ">=40%",
        "hierarchy": "title > visual > explanation",
    })
    new.setdefault("content", "Minimal text supporting the main visual.")
    if not has_visual(new):
        new["visual"] = {"type": "concept", "headline": new.get("one_message") or new.get("page_goal") or new.get("title", "")}
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
    if str(slide.get("title", "")).lower().startswith("details:"):
        return [compact_slide(slide)]
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
            new["title"] = f"{split_names[min(idx, len(split_names)-1)]}: {compact_title(slide.get('title', kind.title()))}"
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
            new["title"] = f"{split_names[min(idx // chunk_size, len(split_names)-1)]}: {compact_title(slide.get('title', kind.title()))}"
            new["page_goal"] = f"{slide.get('page_goal', '')} ({split_names[min(idx // chunk_size, len(split_names)-1)]})"
            new["bullets"] = bullets[idx : idx + chunk_size]
            parts.append(compact_slide(new))
        return parts

    overview = compact_slide(slide)
    overview["content"] = str(overview.get("content", ""))[:120]
    detail = compact_slide(slide)
    detail["title"] = detail_title(slide)
    detail["one_message"] = detail["title"]
    detail["page_goal"] = slide.get("page_goal") or "Explain the supporting detail without crowding the overview slide."
    detail["audience_takeaway"] = slide.get("audience_takeaway") or detail["page_goal"]
    detail["visual"] = {
        "type": "concept",
        "headline": "Supporting detail",
        "insight": str(slide.get("content") or slide.get("body") or "")[:140],
    }
    if kind == "result":
        source_visual = slide.get("visual") or {}
        detail["visual"]["so_what"] = source_visual.get("so_what") or source_visual.get("insight") or "So What: the result supports the paper's core claim."
        detail["visual"]["insight"] = detail["visual"]["so_what"]
    detail["content"] = str(slide.get("content") or slide.get("body") or "Supporting details for the previous slide.")[:220]
    detail["bullets"] = bullets[:2]
    return [overview, detail]


def architecture_report(original: list[dict], planned: list[dict]) -> str:
    lines = ["# Slide Architect Report\n\n"]
    lines.append(f"- Original slide count: {len(original)}\n")
    lines.append(f"- Planned slide count: {len(planned)}\n")
    lines.append("- Rule: prefer adding pages over shrinking fonts.\n")
    lines.append("- Story order: Problem -> Why Existing Work Fails -> Key Insight -> Theory -> Method -> Experiment Logic -> Results -> Takeaways.\n")
    lines.append("- Design rule: one slide one message; visual subject area target >= 40%.\n\n")
    for idx, slide in enumerate(planned, 1):
        cap = capacity_for(slide)
        lines.append(f"## Slide {idx}: {slide.get('title', '')}\n\n")
        lines.append(f"- Story phase: {slide.get('story_phase', infer_story_phase(slide))}\n")
        lines.append(f"- One message: {slide.get('one_message', slide.get('title', ''))}\n")
        lines.append(f"- 5-second takeaway: {slide.get('audience_takeaway', slide.get('page_goal', ''))}\n")
        lines.append(f"- Kind: {slide.get('kind', 'content')}\n")
        lines.append(f"- Layout: {slide.get('layout', slide.get('style', {}).get('layout', 'auto'))}\n")
        lines.append(f"- Bullet count: {len(slide.get('bullets', []) or [])}/{cap['bullets']}\n")
        visual_limit = 6 if (slide.get("visual") or {}).get("type") == "comparison" else cap["steps"]
        lines.append(f"- Visual complexity: {visual_complexity(slide)}/{visual_limit}\n")
        lines.append(f"- Visual area target: {slide.get('visual_area_min', 0.4)}\n")
        lines.append(f"- Page Goal: {slide.get('page_goal', '')}\n")
        lines.append(f"- Visual: {(slide.get('visual') or {}).get('type', 'image/table/text')}\n")
        lines.append(f"- Capacity status: {'PASS' if not overloaded(slide) else 'WARN'}\n\n")
    return "".join(lines)


def architect(spec: dict) -> dict:
    new = deepcopy(spec)
    planned: list[dict] = []
    source_key = "sections" if "sections" in spec else "slides"
    source = [slide for _, slide in sorted(enumerate(spec.get(source_key, [])), key=story_sort_key)]
    for slide in source:
        planned.extend(split_slide(slide))
    new[source_key] = planned
    new.setdefault("planning", {})["slide_architect"] = {
        "original_slide_count": len(spec.get(source_key, [])),
        "planned_slide_count": len(planned),
        "rule": "Plan the page first, then fill content. Prefer splitting pages over shrinking fonts.",
        "story_order": STORY_ORDER,
        "visual_area_min": 0.40,
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
