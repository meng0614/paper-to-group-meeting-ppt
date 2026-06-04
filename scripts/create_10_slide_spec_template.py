#!/usr/bin/env python
import argparse
import json
import re
from pathlib import Path


DEFAULT_TITLES = [
    ("cover", "论文标题与作者信息"),
    ("content", "研究背景与动机"),
    ("content", "核心研究问题"),
    ("content", "现有方法的局限"),
    ("figure", "提出方法概览"),
    ("algorithm", "算法与机制核心"),
    ("content", "实验设计"),
    ("result", "关键实验结果"),
    ("content", "主要贡献总结"),
    ("closing", "局限性与未来工作"),
]


def read_optional(path: Path):
    return path.read_text(encoding="utf-8", errors="ignore") if path and path.exists() else ""


def find_figures(project: Path):
    fig_dir = project / "figures"
    if not fig_dir.exists():
        return []
    return sorted([p.relative_to(project).as_posix() for p in fig_dir.glob("*.png") if not p.name.startswith("_")])


def pick_image(figures, keywords):
    for fig in figures:
        low = fig.lower()
        if any(k in low for k in keywords):
            return fig
    return None


def first_title_from_analysis(text):
    m = re.search(r"(?im)^[-*]\s*Title:\s*(.+)$", text)
    if m:
        return m.group(1).strip()
    m = re.search(r"(?im)^#\s+(.+)$", text)
    return m.group(1).strip() if m else "Paper Group Meeting Presentation"


def make_spec(project: Path, lang: str):
    analysis = read_optional(project / "intermediate" / "paper_analysis.md")
    figures = find_figures(project)
    paper_title = first_title_from_analysis(analysis)

    framework = pick_image(figures, ["framework", "overview", "architecture", "method", "fig_01", "figure_01"])
    algorithm = pick_image(figures, ["alg", "algorithm", "pseudo"])
    setup = pick_image(figures, ["setup", "topology", "parameter", "table"])
    result = pick_image(figures, ["result", "latency", "throughput", "delivery", "convergence", "fig_07", "fig_08"])

    slides = [
        {
            "kind": "cover",
            "title": paper_title,
            "subtitle": "Group Meeting Paper Reading",
            "bullets": ["论文背景", "核心方法", "实验结论"],
            "notes": "介绍论文标题、作者、机构和汇报结构。Source: paper metadata."
        },
        {
            "kind": "content",
            "title": "研究背景与动机",
            "bullets": ["现实需求推动该问题", "现有机制存在不足", "需要新的系统化方法"],
            "notes": "从应用背景进入，说明为什么这个问题值得研究。Source: abstract/introduction."
        },
        {
            "kind": "content",
            "title": "核心研究问题",
            "bullets": ["问题输入是什么", "关键约束是什么", "优化目标是什么"],
            "notes": "讲清楚论文到底要解决什么问题，避免只讲方法。Source: problem formulation."
        },
        {
            "kind": "content",
            "title": "现有方法的局限",
            "bullets": ["假设条件较强", "扩展性存在压力", "难以兼顾性能与保证"],
            "notes": "对应 related work 或 motivation，说明作者为什么需要提出新方法。Source: motivation/related work."
        },
        {
            "kind": "figure",
            "title": "提出方法概览",
            "bullets": ["总体架构分层清晰", "关键模块协同工作", "服务端到端目标"],
            "image": framework,
            "notes": "指向框图，按输入、模块、输出顺序解释。Source: method overview figure."
        },
        {
            "kind": "algorithm",
            "title": "算法与机制核心",
            "bullets": ["定义状态与输入", "执行关键决策步骤", "输出最终策略或结果"],
            "image": algorithm,
            "notes": "解释算法输入、输出、循环逻辑和设计直觉。Source: algorithm/mechanism section."
        },
        {
            "kind": "figure" if setup else "content",
            "title": "实验设计",
            "bullets": ["说明实验平台", "列出 baselines 与指标", "解释关键参数设置"],
            "image": setup,
            "notes": "讲清楚实验是否足以支撑论文结论。Source: evaluation setup."
        },
        {
            "kind": "result",
            "title": "关键实验结果",
            "bullets": ["突出主要趋势", "比较关键 baseline", "说明结果支撑的 claim"],
            "image": result,
            "notes": "先讲指标和 baseline，再讲趋势和结论。Source: evaluation results."
        },
        {
            "kind": "content",
            "title": "主要贡献总结",
            "bullets": ["贡献一：问题建模", "贡献二：核心方法", "贡献三：实验验证"],
            "notes": "把贡献和论文证据对应起来，不要空泛总结。Source: abstract/conclusion."
        },
        {
            "kind": "closing",
            "title": "局限性与未来工作",
            "bullets": ["适用场景仍有限", "实验规模可继续扩大", "可探索更多真实部署"],
            "notes": "用专家视角指出论文没有完全解决的问题，并自然引出讨论。Source: limitations/conclusion."
        },
    ]

    for slide in slides:
        if slide.get("image") is None:
            slide.pop("image", None)

    return {
        "title": paper_title,
        "subtitle": "Generator/Discriminator Group Meeting Deck",
        "language": lang,
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
            "design_system": "academic-rail",
            "animation": "disable"
        },
        "refinement": {"target_score": 8.5},
        "slides": slides,
    }


def main():
    ap = argparse.ArgumentParser(description="Create a 10-slide group-meeting slide_specs.json template from project intermediates.")
    ap.add_argument("--project", type=Path, required=True)
    ap.add_argument("--lang", default="zh")
    ap.add_argument("--out", type=Path, default=None)
    args = ap.parse_args()

    project = args.project.resolve()
    out = args.out or project / "intermediate" / "slide_specs.json"
    spec = make_spec(project, args.lang)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(spec, ensure_ascii=False, indent=2), encoding="utf-8")
    print(out)


if __name__ == "__main__":
    main()
