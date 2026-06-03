#!/usr/bin/env python
import argparse
import json
import shutil
import subprocess
import sys
from copy import deepcopy
from pathlib import Path
from zipfile import ZipFile
import xml.etree.ElementTree as ET

from PIL import Image


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def safe_text_len(text):
    return len(str(text or "").strip())


def classify_image(project: Path, image_rel: str):
    name = Path(image_rel).name.lower()
    if "alg" in name or "algorithm" in name:
        return "algorithm"
    if any(k in name for k in ["result", "plot", "latency", "throughput", "delivery", "convergence", "ablation"]):
        return "result"
    if any(k in name for k in ["table", "setup", "baseline"]):
        return "result"
    try:
        im = Image.open(project / image_rel)
        aspect = im.size[0] / im.size[1]
        if aspect > 1.55:
            return "result"
        if aspect < 0.85:
            return "algorithm"
    except Exception:
        pass
    return "figure"


def judge_slide(project: Path, slide: dict, idx: int):
    issues = []
    tasks = []
    score = 10.0
    bullets = slide.get("bullets", []) or []
    title = slide.get("title", "")
    notes = slide.get("notes", "")
    image = slide.get("image")
    kind = slide.get("kind", "content")

    if safe_text_len(title) < 12:
        score -= 0.6
        issues.append("标题过短，可能不是 assertion headline。")
        tasks.append("把标题改成表达结论的完整句。")
    if safe_text_len(title) > 95:
        score -= 0.4
        issues.append("标题偏长，投影时阅读负担较大。")
        tasks.append("压缩标题，保留一个核心判断。")
    if len(bullets) > 5:
        score -= 0.9
        issues.append("要点超过 5 条，页面可能显得拥挤。")
        tasks.append("合并或删除低价值 bullet，保留 3-5 条。")
    if not bullets and kind not in {"cover"}:
        score -= 0.8
        issues.append("页面缺少解释性 bullet。")
        tasks.append("补充 2-4 条解释图表或方法的 bullet。")
    long_bullets = [b for b in bullets if safe_text_len(b) > 95]
    if long_bullets:
        score -= min(1.2, 0.35 * len(long_bullets))
        issues.append("存在过长 bullet，可能导致排版拥挤。")
        tasks.append("把长 bullet 拆成短句，避免超过一行半。")

    if image:
        img_path = project / image
        if not img_path.exists():
            score -= 1.5
            issues.append(f"图片文件不存在：{image}")
            tasks.append("修正 slide_specs.json 中的 image 路径。")
        else:
            expected_kind = classify_image(project, image)
            if kind == "content":
                score -= 0.4
                issues.append("含图页面仍标记为 content，布局可能不够针对性。")
                tasks.append(f"将 kind 调整为 {expected_kind}。")
            if expected_kind == "algorithm" and len(bullets) < 3:
                score -= 0.5
                issues.append("算法页缺少输入、输出、循环逻辑或 reward/action 解释。")
                tasks.append("为算法页补充输入、输出、关键循环和设计直觉。")
            joined = " ".join(bullets).lower()
            if expected_kind == "result" and not any(k in joined for k in ["metric", "baseline", "result", "ratio", "latency", "throughput", "结果", "指标", "基线"]):
                score -= 0.6
                issues.append("实验结果页没有明确解释指标、基线或结果证明了什么。")
                tasks.append("补充 metric、baseline 和 takeaway。")
    elif kind in {"figure", "algorithm", "result"}:
        score -= 1.0
        issues.append(f"{kind} 页面没有配图。")
        tasks.append("补充对应 figure/table/algorithm/result image。")

    if safe_text_len(notes) < 120:
        score -= 0.8
        issues.append("讲稿过短，学生照着讲可能不顺。")
        tasks.append("补充讲解顺序、图中应指的位置和过渡句。")
    if "Source:" not in notes and "source:" not in notes and "Fig." not in notes:
        score -= 0.4
        issues.append("讲稿缺少来源标记。")
        tasks.append("在 notes 中加入来源页码或章节。")

    scientific = max(1, min(10, round(score + (0.4 if image or kind in {"content", "cover", "closing"} else -0.4), 2)))
    storytelling = max(1, min(10, round(score - (0.5 if safe_text_len(title) < 12 else 0), 2)))
    visual = max(1, min(10, round(score - (0.6 if len(bullets) > 5 else 0), 2)))
    readiness = max(1, min(10, round((scientific + storytelling + visual) / 3 - (0.4 if safe_text_len(notes) < 120 else 0), 2)))
    keep = []
    remove = []
    add = []
    modify = []
    if title:
        keep.append("保留当前页面主题。")
    if image:
        keep.append("保留与论文证据相关的图表。")
    if len(bullets) > 5:
        remove.append("删除或合并低价值 bullet。")
    if long_bullets:
        modify.append("压缩过长 bullet，改成短句。")
    if not image and kind in {"figure", "algorithm", "result"}:
        add.append("补充对应图、表、算法或结果图。")
    if safe_text_len(notes) < 120:
        add.append("补充可口头讲解的 speaker notes。")
    if not add:
        add.append("补充 So What 句，说明本页对论文主张的作用。")
    if not modify:
        modify.append("检查标题是否能表达一个明确结论。")

    return {
        "slide": idx,
        "title": title,
        "score": max(0, round(score, 2)),
        "scores": {
            "Scientific Accuracy": scientific,
            "Storytelling": storytelling,
            "Visual Quality": visual,
            "Presentation Readiness": readiness,
        },
        "advice": {
            "KEEP": keep,
            "REMOVE": remove or ["无必须删除项。"],
            "ADD": add,
            "MODIFY": modify,
            "REGENERATE": "yes" if readiness < 8 or issues else "no",
        },
        "issues": issues,
        "revision_tasks": tasks,
    }


def judge_deck(project: Path, spec: dict):
    slides = spec.get("slides", [])
    slide_reports = [judge_slide(project, s, i + 1) for i, s in enumerate(slides)]
    avg = sum(r["score"] for r in slide_reports) / max(1, len(slide_reports))
    dim_names = ["Scientific Accuracy", "Storytelling", "Visual Quality", "Presentation Readiness"]
    dim_avgs = {
        d: round(sum(r["scores"][d] for r in slide_reports) / max(1, len(slide_reports)), 2)
        for d in dim_names
    }
    major = []
    tasks = []
    for r in slide_reports:
        for issue in r["issues"][:2]:
            major.append(f"Slide {r['slide']}: {issue}")
        for task in r["revision_tasks"][:2]:
            tasks.append({"slide": r["slide"], "priority": "high" if r["score"] < 7.0 else "medium", "action": task})
    return {
        "overall_score": round(avg, 2),
        "dimensions": {
            **dim_avgs,
            "Audience Perspective": round((dim_avgs["Storytelling"] + dim_avgs["Presentation Readiness"]) / 2, 2),
            "Group Meeting Perspective": round((dim_avgs["Scientific Accuracy"] + dim_avgs["Presentation Readiness"]) / 2, 2),
            "figure_selection": round(sum(1 for s in slides if s.get("image")) / max(1, len(slides)) * 10, 2),
            "speaker_notes": round(sum(1 for s in slides if safe_text_len(s.get("notes")) >= 120) / max(1, len(slides)) * 10, 2),
        },
        "major_issues": major[:12],
        "revision_tasks": tasks[:16],
        "slides": slide_reports,
    }


def split_long_bullet(text, limit=92):
    text = str(text).strip()
    if len(text) <= limit:
        return [text]
    for sep in ["；", ";", "，", ",", "。", "."]:
        parts = [p.strip() for p in text.split(sep) if p.strip()]
        if len(parts) >= 2 and all(len(p) <= limit for p in parts):
            return parts[:2]
    return [text[:limit].rstrip() + "..."]


def revise_spec(project: Path, spec: dict, report: dict):
    new = deepcopy(spec)
    for slide in new.get("slides", []):
        bullets = slide.get("bullets", []) or []
        revised = []
        for b in bullets:
            revised.extend(split_long_bullet(b))
        slide["bullets"] = revised[:5]
        if slide.get("image"):
            slide["kind"] = classify_image(project, slide["image"])
        if safe_text_len(slide.get("notes")) < 120:
            slide["notes"] = (slide.get("notes", "").strip() + " 讲解时先说明本页核心观点，再指向图表中的关键区域，最后用一句话过渡到下一页。").strip()
        if slide.get("image") and ("Source:" not in slide.get("notes", "") and "Fig." not in slide.get("notes", "")):
            slide["notes"] += f" Source: {slide.get('image')}."
    new.setdefault("refinement", {})
    new["refinement"]["last_reviewer_score"] = report["overall_score"]
    return new


def write_markdown_report(path: Path, report: dict):
    lines = ["# Reviewer Report\n\n", f"Overall score: {report['overall_score']}/10\n\n"]
    lines.append("## Dimension Scores\n\n")
    for k, v in report["dimensions"].items():
        lines.append(f"- {k}: {v}\n")
    lines.append("\n## Major Issues\n\n")
    for issue in report["major_issues"]:
        lines.append(f"- {issue}\n")
    lines.append("\n## Revision Tasks\n\n")
    for task in report["revision_tasks"]:
        lines.append(f"- Slide {task['slide']} ({task['priority']}): {task['action']}\n")
    lines.append("\n## Slide Scores\n\n")
    for s in report["slides"]:
        lines.append(f"### Slide {s['slide']}: {s['title']}\n\n")
        for k, v in s["scores"].items():
            lines.append(f"- {k}: {v}/10\n")
        lines.append("- KEEP:\n")
        for item in s["advice"]["KEEP"]:
            lines.append(f"  - {item}\n")
        lines.append("- REMOVE:\n")
        for item in s["advice"]["REMOVE"]:
            lines.append(f"  - {item}\n")
        lines.append("- ADD:\n")
        for item in s["advice"]["ADD"]:
            lines.append(f"  - {item}\n")
        lines.append("- MODIFY:\n")
        for item in s["advice"]["MODIFY"]:
            lines.append(f"  - {item}\n")
        lines.append(f"- REGENERATE: {s['advice']['REGENERATE']}\n\n")
    path.write_text("".join(lines), encoding="utf-8")


def validate_pptx(pptx: Path):
    with ZipFile(pptx) as z:
        bad = z.testzip()
        if bad:
            raise RuntimeError(f"Bad zip entry: {bad}")
        names = z.namelist()
        for name in names:
            if name.endswith(".xml"):
                ET.fromstring(z.read(name))
        return {
            "slides": len([n for n in names if n.startswith("ppt/slides/slide") and n.endswith(".xml")]),
            "images": len([n for n in names if n.startswith("ppt/media/")]),
            "size": pptx.stat().st_size,
        }


def copy_project_assets(project: Path, round_dir: Path):
    for name in ["figures", "source"]:
        src = project / name
        dst = round_dir / name
        if src.exists() and not dst.exists():
            shutil.copytree(src, dst)


def run_build(script_dir: Path, spec_path: Path, out_dir: Path):
    build_script = script_dir / "build_pptx_from_spec.py"
    subprocess.run([sys.executable, str(build_script), "--spec", str(spec_path), "--out", str(out_dir)], check=True)


def main():
    ap = argparse.ArgumentParser(description="Run a generator-reviewer-reviser loop for paper group-meeting PPT slide specs.")
    ap.add_argument("--project", type=Path, required=True, help="Project dir containing figures/ and intermediate/slide_specs.json.")
    ap.add_argument("--rounds", type=int, default=3)
    ap.add_argument("--target-score", type=float, default=8.5)
    args = ap.parse_args()

    project = args.project.resolve()
    script_dir = Path(__file__).resolve().parent
    spec = load_json(project / "intermediate" / "slide_specs.json")
    runs = project / "runs"
    final = project / "final"
    runs.mkdir(parents=True, exist_ok=True)
    history = []

    for r in range(1, args.rounds + 1):
        round_dir = runs / f"round_{r:02d}"
        round_dir.mkdir(parents=True, exist_ok=True)
        copy_project_assets(project, round_dir)
        spec_path = round_dir / "slide_specs.json"
        write_json(spec_path, spec)
        run_build(script_dir, spec_path, round_dir)
        validation = validate_pptx(round_dir / "final_presentation.pptx")
        report = judge_deck(round_dir, spec)
        report["pptx_validation"] = validation
        write_json(round_dir / "reviewer_report.json", report)
        write_markdown_report(round_dir / "reviewer_report.md", report)
        (round_dir / "revision_plan.md").write_text(
            "\n".join([f"- Slide {t['slide']} ({t['priority']}): {t['action']}" for t in report["revision_tasks"]]),
            encoding="utf-8",
        )
        history.append({"round": r, "score": report["overall_score"], "validation": validation})
        key_dims = ["Scientific Accuracy", "Storytelling", "Visual Quality", "Presentation Readiness"]
        if all(float(report["dimensions"].get(k, 0)) >= args.target_score for k in key_dims):
            break
        spec = revise_spec(round_dir, spec, report)

    best_round = max(history, key=lambda x: x["score"])["round"]
    best_dir = runs / f"round_{best_round:02d}"
    if final.exists():
        shutil.rmtree(final)
    shutil.copytree(best_dir, final)
    if (final / "reviewer_report.md").exists():
        shutil.copy2(final / "reviewer_report.md", final / "review_report.md")
        shutil.copy2(final / "reviewer_report.md", project / "review_report.md")
    (project / "improvement_history.md").write_text(
        "# Improvement History\n\n" + "\n".join([f"- Round {h['round']}: score {h['score']}/10, slides {h['validation']['slides']}, images {h['validation']['images']}" for h in history]) + "\n",
        encoding="utf-8",
    )
    print(final / "final_presentation.pptx")
    print(f"best_round={best_round}")


if __name__ == "__main__":
    main()
