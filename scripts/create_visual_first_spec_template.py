#!/usr/bin/env python
from __future__ import annotations

import argparse
import json
from pathlib import Path


STORY_SLIDES = [
    ("cover", "Problem", "Paper title: one-sentence positioning", "Audience knows the paper's core problem and why it is worth hearing."),
    ("problem", "Problem", "The real-world situation creates a new pressure", "Audience sees why the work matters before seeing the method."),
    ("problem", "Challenge", "Existing assumptions break in the target setting", "Audience remembers the mismatch between old methods and the paper setting."),
    ("method", "Idea", "Key idea: reframe the hard problem into a tractable decision flow", "Audience understands the core insight in one sentence."),
    ("method", "Method", "Framework: how the idea becomes a system or algorithm", "Audience can explain the whole method in 30 seconds."),
    ("algorithm", "Method", "Mechanism: the key decision logic", "Audience understands why the algorithm steps exist."),
    ("experiment", "Result", "Experiment design: how the claim is tested", "Audience sees setup, baselines, metrics, and claim as one validation chain."),
    ("result", "Result", "Main result: the method changes the key metric", "Audience remembers the main improvement and its meaning."),
    ("result", "Result", "Result insight: so what?", "Audience understands what the result enables or proves."),
    ("closing", "Takeaway", "Takeaways: contribution, novelty, limitation", "Audience leaves with the strongest contribution and honest limitation."),
]


def make_slide(kind: str, phase: str, title: str, takeaway: str, idx: int) -> dict:
    visual_type = {
        "cover": "concept",
        "problem": "comparison" if phase == "Challenge" else "pipeline",
        "method": "pipeline",
        "algorithm": "flow",
        "experiment": "pipeline",
        "result": "result_bar",
        "closing": "concept",
    }.get(kind, "concept")
    visual: dict = {"type": visual_type, "insight": "Replace this with the paper-specific visual insight."}
    if visual_type in {"pipeline", "flow"}:
        visual["steps"] = [
            {"label": "Context", "detail": "Replace with paper-specific element."},
            {"label": "Decision", "detail": "Replace with paper-specific element."},
            {"label": "Outcome", "detail": "Replace with paper-specific element."},
        ]
    elif visual_type == "comparison":
        visual.update({
            "left_title": "Existing",
            "right_title": "Target setting",
            "left": ["Old assumption", "Old mechanism"],
            "right": ["New constraint", "New requirement"],
        })
    elif visual_type == "result_bar":
        visual.update({
            "items": [
                {"label": "Baseline", "value": 70},
                {"label": "Proposed", "value": 88, "highlight": True},
            ],
            "unit": "%",
            "so_what": "So What: explain what the improvement enables.",
        })
    else:
        visual["headline"] = takeaway
    return {
        "kind": kind,
        "section": phase,
        "story_phase": phase,
        "title": title,
        "one_message": title,
        "audience_takeaway": takeaway,
        "page_goal": takeaway,
        "visual_area_min": 0.4,
        "visual": visual,
        "content": "Minimal explanation supporting the visual. Replace after paper understanding.",
        "bullets": ["Replace with one short support point", "Replace with one short support point"],
        "notes": f"Slide {idx}: explain the visual first, then the text. Do not read a paper summary.",
    }


def template() -> dict:
    slides = [make_slide(kind, phase, title, takeaway, i + 1) for i, (kind, phase, title, takeaway) in enumerate(STORY_SLIDES)]
    return {
        "title": "Visual-first Academic Presentation",
        "subtitle": "Story-first group meeting deck",
        "language": "zh",
        "style": {
            "primary_color": "111827",
            "secondary_color": "2563EB",
            "accent_color": "DC2626",
            "neutral_color": "6B7280",
            "light_color": "F8FAFC",
            "title_font": "Microsoft YaHei",
            "body_font": "Microsoft YaHei",
            "title_size": 30,
            "body_size": 19,
            "layout": "visual-first",
            "animation": "disable",
            "design_system": "academic-rail",
        },
        "reference_design_philosophy": {
            "policy": "Learn reference PPT design philosophy only; do not copy colors or fonts.",
            "story_order": ["Problem", "Challenge", "Idea", "Method", "Result", "Takeaway"],
            "visual_area_min": 0.4,
            "learned_patterns": [
                "stable master frame",
                "clear title hierarchy",
                "visual-text zoning",
                "disciplined whitespace",
                "limited color roles",
                "chapter rhythm"
            ],
        },
        "slides": slides,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Create a story-first, visual-first slide spec template.")
    parser.add_argument("--project", type=Path, required=True)
    parser.add_argument("--lang", choices=["zh", "en"], default="zh")
    args = parser.parse_args()
    out = args.project / "intermediate" / "slide_specs.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(template(), ensure_ascii=False, indent=2), encoding="utf-8")
    print(out)


if __name__ == "__main__":
    main()
