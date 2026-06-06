#!/usr/bin/env python
from __future__ import annotations

import argparse
import json
from pathlib import Path

from generate_academic_presentation import build_understanding


def main() -> None:
    parser = argparse.ArgumentParser(description="Build Research Understanding Engine artifacts for a paper PDF.")
    parser.add_argument("--pdf", type=Path, required=True)
    parser.add_argument("--project", type=Path, required=True)
    parser.add_argument("--lang", choices=["zh", "en"], default="zh")
    args = parser.parse_args()

    project = args.project.resolve()
    intermediate = project / "intermediate"
    intermediate.mkdir(parents=True, exist_ok=True)
    understanding = build_understanding(args.pdf.resolve(), args.lang)
    (intermediate / "research_understanding.json").write_text(json.dumps(understanding, ensure_ascii=False, indent=2), encoding="utf-8")
    (intermediate / "research_story_brief.md").write_text(
        "# Research Story Brief\n\n"
        + understanding["research_story_brief"]["one_sentence"]
        + "\n\n## Storyline\n"
        + "\n".join(f"- {row['phase']}: {row['message']}" for row in understanding["research_story_brief"]["storyline"])
        + "\n",
        encoding="utf-8",
    )
    (intermediate / "storyline_extraction.md").write_text(
        "# Storyline Extraction\n\n"
        + "\n".join(
            f"## {key}\n\n{value if not isinstance(value, (dict, list)) else json.dumps(value, ensure_ascii=False, indent=2)}\n"
            for key, value in understanding.get("storyline_extraction", {}).items()
        ),
        encoding="utf-8",
    )
    (intermediate / "figure_roles.md").write_text(
        "# Figure-Centric Understanding\n\n"
        + "\n".join(f"- {role}: {label or 'not found'}" for role, label in understanding.get("figure_roles", {}).items())
        + "\n",
        encoding="utf-8",
    )
    (intermediate / "theory_model.md").write_text(
        "# Theory Compression\n\n"
        + "\n".join(
            f"## {key.replace('_', ' ').title()}\n\n{value if not isinstance(value, list) else json.dumps(value, ensure_ascii=False, indent=2)}\n"
            for key, value in understanding.get("theory_model", {}).items()
        ),
        encoding="utf-8",
    )
    (intermediate / "experiment_logic.md").write_text(
        "# Experiment Logic Reconstruction\n\n"
        + "\n\n".join(
            "## "
            + str(card.get("type", "experiment")).title()
            + "\n\n"
            + "\n".join(
                f"- {key.title()}: {card.get(key, '')}"
                for key in ["question", "setup", "evidence", "conclusion"]
            )
            for card in understanding.get("experiment_logic", [])
        )
        + "\n",
        encoding="utf-8",
    )
    (intermediate / "professor_gate.md").write_text(
        "# Professor Gate\n\n"
        + json.dumps(understanding.get("professor_gate", {}), ensure_ascii=False, indent=2)
        + "\n",
        encoding="utf-8",
    )
    (intermediate / "paper_analysis.md").write_text(
        "# Paper Analysis\n\n"
        + f"- Title: {understanding['title']}\n"
        + f"- Authors: {', '.join(understanding.get('authors') or [])}\n\n"
        + "## Why / What / How / Why Effective / How Verified\n\n"
        + json.dumps(understanding["research_questions"], ensure_ascii=False, indent=2)
        + "\n",
        encoding="utf-8",
    )
    print(intermediate / "research_understanding.json")


if __name__ == "__main__":
    main()
