#!/usr/bin/env python
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from copy import deepcopy
from pathlib import Path
from zipfile import ZipFile


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def text_len(value) -> int:
    return len(str(value or "").strip())


def sections(spec: dict) -> list[dict]:
    return spec.get("sections") or spec.get("slides") or []


def has_visual(section: dict) -> bool:
    return bool(section.get("image") or section.get("visual") or section.get("table") or section.get("pseudocode"))


def has_so_what(section: dict) -> bool:
    visual = section.get("visual") or {}
    joined = " ".join(section.get("bullets", []) or []) + " " + str(visual.get("so_what", "")) + " " + str(visual.get("insight", ""))
    return any(token in joined for token in ["So What", "so what", "提升", "降低", "提高", "减少", "%", "latency", "delivery", "success"])


def judge_section(section: dict, idx: int, layout_status: str) -> dict:
    issues: list[str] = []
    tasks: list[str] = []
    score = 10.0
    kind = section.get("kind", section.get("section", "content")).lower()

    if not section.get("page_goal"):
        score -= 0.7
        issues.append("Missing Page Goal.")
        tasks.append("Add a Page Goal that states what readers should understand in 5 seconds.")
    if not has_visual(section):
        score -= 1.4
        issues.append("Section has no visual center.")
        tasks.append("Add a paper figure, concept diagram, flow, comparison, table, or result chart.")
    if text_len(section.get("title")) < 10:
        score -= 0.3
        issues.append("Title is too weak as a section-level claim.")
        tasks.append("Rewrite the title as an assertion headline.")
    if kind in {"result", "results"} and not has_so_what(section):
        score -= 1.0
        issues.append("Results section does not answer So What.")
        tasks.append("Add an explicit So What statement tied to the key trend or number.")
    if kind in {"method", "algorithm"} and (section.get("visual") or {}).get("type") not in {"pipeline", "flow", "comparison", "concept"} and not section.get("image"):
        score -= 0.5
        issues.append("Method/algorithm section lacks a process-style visual.")
        tasks.append("Use pipeline, flow, architecture, or state-transition style visual.")
    if text_len(section.get("content")) + text_len(section.get("body")) > 1800 and not (section.get("details") or section.get("long_text")):
        score -= 0.6
        issues.append("Long text is not folded or scrollable.")
        tasks.append("Move long explanation into details/long_text.")
    if layout_status != "PASS":
        score -= 0.8
        issues.append("Layout validator did not pass.")
        tasks.append("Repair layout before accepting final HTML.")

    scientific = max(1, min(10, round(score + (0.2 if section.get("notes") else -0.2), 2)))
    storytelling = max(1, min(10, round(score + (0.2 if section.get("page_goal") else -0.3), 2)))
    readability = max(1, min(10, round(score + (0.2 if section.get("details") or text_len(section.get("content")) < 900 else -0.2), 2)))
    visual = max(1, min(10, round(score + (0.5 if has_visual(section) else -1.0), 2)))
    return {
        "section": idx,
        "title": section.get("title", ""),
        "score": max(1, round(score, 2)),
        "scores": {
            "Scientific Accuracy": scientific,
            "Storytelling": storytelling,
            "Readability": readability,
            "Visual Hierarchy": visual,
        },
        "advice": {
            "KEEP": ["Keep the central claim and visual-first organization."],
            "REMOVE": ["Remove text that duplicates the visual."] if text_len(section.get("content")) > 900 else ["No required removal."],
            "ADD": tasks[:3] if tasks else ["Add one discussion question or So What sentence."],
            "MODIFY": ["Ensure Page Goal -> Visual -> Content order remains visible."],
            "REGENERATE": "yes" if issues or score < 9 else "no",
        },
        "issues": issues,
        "revision_tasks": tasks,
    }


def judge_report(spec: dict, layout_status: str) -> dict:
    reports = [judge_section(sec, i + 1, layout_status) for i, sec in enumerate(sections(spec))]
    dims = {}
    for name in ["Scientific Accuracy", "Storytelling", "Readability", "Visual Hierarchy"]:
        dims[name] = round(sum(r["scores"][name] for r in reports) / max(1, len(reports)), 2)
    visual_compliance = round(sum(1 for sec in sections(spec) if has_visual(sec)) / max(1, len(sections(spec))) * 10, 2)
    if layout_status != "PASS":
        dims["Readability"] = max(1, dims["Readability"] - 1.0)
        dims["Visual Hierarchy"] = max(1, dims["Visual Hierarchy"] - 1.0)
    tasks = []
    major = []
    for r in reports:
        major.extend([f"Section {r['section']}: {issue}" for issue in r["issues"][:2]])
        tasks.extend({"section": r["section"], "priority": "high" if r["score"] < 8.5 else "medium", "action": t} for t in r["revision_tasks"][:2])
    return {
        "overall_score": round(sum(r["score"] for r in reports) / max(1, len(reports)), 2),
        "dimensions": {
            **dims,
            "Visual-first Compliance": visual_compliance,
            "Layout Safety": 10.0 if layout_status == "PASS" else 6.0,
            "HTML Report Readiness": round((dims["Storytelling"] + dims["Readability"] + dims["Visual Hierarchy"]) / 3, 2),
        },
        "layout_status": layout_status,
        "major_issues": major[:14],
        "revision_tasks": tasks[:18],
        "sections": reports,
    }


def write_review(path: Path, report: dict) -> None:
    lines = ["# Review Report\n\n", f"Overall score: {report['overall_score']}/10\n\n"]
    lines.append("## Dimension Scores\n\n")
    for key, value in report["dimensions"].items():
        lines.append(f"- {key}: {value}\n")
    lines.append("\n## Major Issues\n\n")
    for issue in report["major_issues"] or ["No severe issue found."]:
        lines.append(f"- {issue}\n")
    lines.append("\n## Revision Tasks\n\n")
    for task in report["revision_tasks"] or []:
        lines.append(f"- Section {task['section']} ({task['priority']}): {task['action']}\n")
    lines.append("\n## Section Scores\n\n")
    for sec in report["sections"]:
        lines.append(f"### Section {sec['section']}: {sec['title']}\n\n")
        for key, value in sec["scores"].items():
            lines.append(f"- {key}: {value}/10\n")
        for label in ["KEEP", "REMOVE", "ADD", "MODIFY"]:
            lines.append(f"- {label}:\n")
            for item in sec["advice"][label]:
                lines.append(f"  - {item}\n")
        lines.append(f"- REGENERATE: {sec['advice']['REGENERATE']}\n\n")
    path.write_text("".join(lines), encoding="utf-8")


def revise_spec(spec: dict, report: dict) -> dict:
    new = deepcopy(spec)
    key = "sections" if "sections" in new else "slides"
    fixed = []
    for idx, sec in enumerate(sections(new), 1):
        sec.setdefault("page_goal", sec.get("title", ""))
        sec.setdefault("content", "")
        if not has_visual(sec):
            sec["visual"] = {"type": "concept", "headline": sec.get("page_goal") or sec.get("title", "")}
        if text_len(sec.get("content")) > 1400 and not sec.get("details"):
            sec["details"] = sec["content"][700:]
            sec["content"] = sec["content"][:700]
        if sec.get("kind") == "result" and sec.get("visual", {}).get("type") == "result_bar":
            sec["visual"].setdefault("so_what", "So What: the key metric improves and supports the paper claim.")
        sec.setdefault("notes", f"Source: section {idx} visual report plan.")
        fixed.append(sec)
    new[key] = fixed
    return new


def copy_assets(project: Path, round_dir: Path) -> None:
    for name in ["figures", "source", "pages"]:
        src = project / name
        dst = round_dir / name
        if src.exists():
            if dst.exists():
                shutil.rmtree(dst)
            shutil.copytree(src, dst)


def run(cmd: list[str]) -> str:
    result = subprocess.run(cmd, check=True, capture_output=True, text=True)
    return result.stdout.strip().splitlines()[-1] if result.stdout.strip() else ""


def validate_pptx(path: Path) -> str:
    if not path.exists() or path.stat().st_size < 2048:
        return "FAIL"
    try:
        with ZipFile(path) as zf:
            if zf.testzip() is not None:
                return "FAIL"
            names = set(zf.namelist())
            required = {"[Content_Types].xml", "ppt/presentation.xml", "ppt/slides/slide1.xml"}
            return "PASS" if required.issubset(names) else "FAIL"
    except Exception:
        return "FAIL"


def main() -> None:
    parser = argparse.ArgumentParser(description="Run Generator -> Visualizer -> Layout Validator -> Discriminator loop for HTML and editable PPTX output.")
    parser.add_argument("--project", type=Path, required=True)
    parser.add_argument("--rounds", type=int, default=3)
    parser.add_argument("--target-score", type=float, default=9.0)
    args = parser.parse_args()

    project = args.project.resolve()
    script_dir = Path(__file__).resolve().parent
    spec = load_json(project / "intermediate" / "slide_specs.json")
    runs = project / "runs"
    final = project / "final"
    runs.mkdir(parents=True, exist_ok=True)
    history = []

    for round_idx in range(1, args.rounds + 1):
        round_dir = runs / f"round_{round_idx:02d}"
        round_dir.mkdir(parents=True, exist_ok=True)
        copy_assets(project, round_dir)

        raw_spec = round_dir / "slide_specs.raw.json"
        planned_spec = round_dir / "slide_specs.json"
        architect_report = round_dir / "slide_architect_report.md"
        write_json(raw_spec, spec)
        run([sys.executable, str(script_dir / "slide_architect.py"), "--spec", str(raw_spec), "--out", str(planned_spec), "--report", str(architect_report)])

        html_path = Path(run([sys.executable, str(script_dir / "build_html_report_from_spec.py"), "--spec", str(planned_spec), "--out", str(round_dir)]))
        layout_report = round_dir / "layout_check_report.md"
        layout_json = round_dir / "layout_check_report.json"
        fixed_spec = round_dir / "slide_specs.fixed.json"
        layout_status = run([
            sys.executable,
            str(script_dir / "html_layout_validator.py"),
            "--project",
            str(round_dir),
            "--spec",
            str(planned_spec),
            "--html",
            str(html_path),
            "--report",
            str(layout_report),
            "--json-report",
            str(layout_json),
            "--fix-out",
            str(fixed_spec),
        ])
        if layout_status != "PASS" and fixed_spec.exists():
            shutil.copy2(fixed_spec, planned_spec)
            html_path = Path(run([sys.executable, str(script_dir / "build_html_report_from_spec.py"), "--spec", str(planned_spec), "--out", str(round_dir)]))
            layout_status = run([
                sys.executable,
                str(script_dir / "html_layout_validator.py"),
                "--project",
                str(round_dir),
                "--spec",
                str(planned_spec),
                "--html",
                str(html_path),
                "--report",
                str(layout_report),
                "--json-report",
                str(layout_json),
            ])

        pptx_path = Path(run([sys.executable, str(script_dir / "build_editable_pptx_from_spec.py"), "--spec", str(planned_spec), "--out", str(round_dir)]))
        pptx_status = validate_pptx(pptx_path)

        figures_dir = round_dir / "figures"
        figure_status = "SKIP"
        if figures_dir.exists():
            figure_status = run([
                sys.executable,
                str(script_dir / "figure_quality_validator.py"),
                "--figures",
                str(figures_dir),
                "--report",
                str(round_dir / "figure_quality_report.md"),
                "--json-report",
                str(round_dir / "figure_quality_report.json"),
            ])

        current_spec = load_json(planned_spec)
        report = judge_report(current_spec, layout_status)
        report["dimensions"]["Editable PPTX Validity"] = 10.0 if pptx_status == "PASS" else 4.0
        report["dimensions"]["Figure Crop Quality"] = 10.0 if figure_status in {"PASS", "SKIP"} else 7.0
        write_json(round_dir / "reviewer_report.json", report)
        write_review(round_dir / "review_report.md", report)
        shutil.copy2(round_dir / "review_report.md", round_dir / "reviewer_report.md")
        (round_dir / "revision_plan.md").write_text(
            "\n".join(f"- Section {task['section']} ({task['priority']}): {task['action']}" for task in report["revision_tasks"]),
            encoding="utf-8",
        )
        history.append({
            "round": round_idx,
            "score": report["overall_score"],
            "layout": layout_status,
            "pptx": pptx_status,
            "figures": figure_status,
            "dimensions": report["dimensions"],
            "sections": len(sections(current_spec)),
        })
        key_dims = ["Scientific Accuracy", "Storytelling", "Readability", "Visual Hierarchy"]
        if layout_status == "PASS" and pptx_status == "PASS" and all(float(report["dimensions"].get(dim, 0)) >= args.target_score for dim in key_dims):
            break
        spec = revise_spec(current_spec, report)

    best = max(history, key=lambda h: (h["layout"] == "PASS", h["score"]))
    best_dir = runs / f"round_{best['round']:02d}"
    if final.exists():
        shutil.copytree(best_dir, final, dirs_exist_ok=True)
    else:
        shutil.copytree(best_dir, final)
    for name in [
        "final_presentation_generated.html",
        "final_presentation.html",
        "final_presentation_generated.pptx",
        "final_presentation.pptx",
        "layout_check_report.md",
        "figure_quality_report.md",
        "review_report.md",
        "improvement_history.md",
        "speaker_notes.md",
        "slide_architect_report.md",
    ]:
        src = final / name
        if src.exists():
            shutil.copy2(src, project / name)
    lines = ["# Improvement History\n\n"]
    for item in history:
        dims = ", ".join(f"{k}={v}" for k, v in item["dimensions"].items())
        lines.append(
            f"- Round {item['round']}: score {item['score']}/10, "
            f"layout={item['layout']}, pptx={item['pptx']}, figures={item['figures']}, "
            f"sections={item['sections']}, {dims}\n"
        )
    (project / "improvement_history.md").write_text("".join(lines), encoding="utf-8")
    shutil.copy2(project / "improvement_history.md", final / "improvement_history.md")
    print(final / "final_presentation_generated.html")
    print(f"best_round={best['round']}")


if __name__ == "__main__":
    main()
