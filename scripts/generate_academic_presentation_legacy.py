#!/usr/bin/env python
from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

from pypdf import PdfReader


LIGATURES = {
    "\ufb00": "ff",
    "\ufb01": "fi",
    "\ufb02": "fl",
    "\ufb03": "ffi",
    "\ufb04": "ffl",
}

STORY_ORDER = ["Problem", "Challenge", "Idea", "Method", "Result", "Takeaway"]


@dataclass
class FigureCaption:
    label: str
    page: int
    caption: str


def clean_text(text: str) -> str:
    for src, dst in LIGATURES.items():
        text = text.replace(src, dst)
    text = text.replace("\u2013", "-").replace("\u2014", "-")
    return re.sub(r"[ \t]+", " ", text)


def compact(value: str, limit: int = 180) -> str:
    text = re.sub(r"\s+", " ", str(value or "")).strip()
    if len(text) <= limit:
        return text
    return text[:limit].rstrip(" ,;:.") + "..."


def split_sentences(text: str) -> list[str]:
    text = re.sub(r"\s+", " ", text)
    parts = re.split(r"(?<=[.!?])\s+(?=[A-Z0-9])", text)
    return [p.strip() for p in parts if len(p.strip()) > 25]


def first_matching(sentences: list[str], keywords: list[str], limit: int = 2) -> list[str]:
    matches = []
    lowered = [(s, s.lower()) for s in sentences]
    for sentence, low in lowered:
        if any(k.lower() in low for k in keywords):
            matches.append(sentence)
        if len(matches) >= limit:
            break
    return matches


def extract_pages(pdf: Path) -> list[str]:
    reader = PdfReader(str(pdf))
    pages = []
    for page in reader.pages:
        pages.append(clean_text(page.extract_text() or ""))
    return pages


def extract_title(first_page: str, pdf: Path) -> str:
    lines = [clean_text(line).strip() for line in first_page.splitlines() if line.strip()]
    lines = [line for line in lines if not re.search(r"@|accepted for|copyright|personal use|proc\.|university|abstract", line, re.I)]
    if not lines:
        return pdf.stem
    title_lines = []
    for line in lines[:8]:
        if re.search(r"^[A-Z][a-z]+ [A-Z]", line) and len(title_lines) >= 2:
            break
        if len(line) > 90:
            continue
        title_lines.append(line)
        if len(title_lines) >= 3:
            break
    title = " ".join(title_lines[:3]).strip()
    return title or pdf.stem


def extract_authors(first_page: str, title: str) -> list[str]:
    lines = [clean_text(line).strip() for line in first_page.splitlines() if line.strip()]
    authors = []
    title_tokens = set(title.split())
    for line in lines[:30]:
        if line in title or set(line.split()).issubset(title_tokens):
            continue
        if re.search(r"@|university|accepted|copyright|abstract|proc\.|ieee", line, re.I):
            continue
        words = line.split()
        if 2 <= len(words) <= 4 and all(re.match(r"^[A-Z][A-Za-z.\-`'\u00c0-\u017f]+$", w) for w in words):
            authors.append(line)
        if len(authors) >= 5:
            break
    return authors


def extract_abstract(full_text: str) -> str:
    patterns = [
        r"Abstract\s*[-\u2014]?\s*(.*?)(?:Index Terms|I\.\s+INTRODUCTION)",
        r"ABSTRACT\s*(.*?)(?:KEYWORDS|1\s+Introduction)",
    ]
    for pattern in patterns:
        match = re.search(pattern, full_text, re.I | re.S)
        if match:
            return compact(match.group(1), 1200)
    return compact(full_text, 900)


def extract_figure_captions(pages: list[str]) -> list[FigureCaption]:
    figures: list[FigureCaption] = []
    seen = set()
    for page_no, text in enumerate(pages, 1):
        lines = [clean_text(line).strip() for line in text.splitlines() if line.strip()]
        for idx, line in enumerate(lines):
            match = re.match(r"^(Fig\.?|Figure)\s+(\d+[A-Za-z]?)\.?\s*(.*)$", line, re.I)
            if not match:
                continue
            number = match.group(2)
            label = f"Fig. {number}"
            if (page_no, label) in seen:
                continue
            tail = match.group(3).strip()
            caption_parts = [tail] if tail else []
            for extra in lines[idx + 1 : idx + 3]:
                if re.match(r"^(Fig\.?|Figure)\s+\d+", extra, re.I):
                    break
                if re.match(r"^[A-Z]\.\s+", extra):
                    break
                if len(extra) < 140 and not re.search(r"^(I+V?|V?I+)\.", extra):
                    caption_parts.append(extra)
            caption = compact(" ".join(caption_parts), 260)
            figures.append(FigureCaption(label=label, page=page_no, caption=caption))
            seen.add((page_no, label))
    return figures


def choose_figures(figures: list[FigureCaption]) -> dict[str, FigureCaption | None]:
    def pick(words: list[str], fallback: int = 0) -> FigureCaption | None:
        for fig in figures:
            low = fig.caption.lower()
            if any(word.lower() in low for word in words):
                return fig
        return figures[fallback] if len(figures) > fallback else (figures[0] if figures else None)

    return {
        "background": pick(["system", "architecture", "framework", "overview", "network", "topology", "pipeline"], 0),
        "idea": pick(["idea", "framework", "model", "solution", "overview", "conflict graph", "independent vertex"], 1 if len(figures) > 1 else 0),
        "method": pick(["algorithm", "method", "workflow", "pipeline", "architecture", "iterative", "candidate"], 0),
        "experiment": pick(["experiment", "setup", "dataset", "testbed", "topology", "benchmark", "nodes"], -1 if figures else 0),
        "result": pick(["result", "runtime", "performance", "comparison", "latency", "throughput", "memory", "varying", "normalized"], -1 if figures else 0),
    }


def write_markdown(path: Path, lines: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(lines), encoding="utf-8")


def run(cmd: list[str], cwd: Path | None = None, allow_fail: bool = False) -> str:
    result = subprocess.run(cmd, cwd=str(cwd) if cwd else None, capture_output=True, text=True)
    if result.returncode != 0 and not allow_fail:
        raise RuntimeError(f"Command failed: {' '.join(cmd)}\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}")
    return (result.stdout or "").strip()


def ensure_project(pdf: Path, project: Path) -> Path:
    project.mkdir(parents=True, exist_ok=True)
    source = project / "source"
    source.mkdir(parents=True, exist_ok=True)
    dst = source / "paper.pdf"
    if pdf.resolve() != dst.resolve():
        shutil.copy2(pdf, dst)
    for name in ["pages", "figures", "intermediate"]:
        (project / name).mkdir(parents=True, exist_ok=True)
    return dst


def render_pages(script_dir: Path, pdf: Path, project: Path, dpi: int) -> None:
    pages_dir = project / "pages"
    if list(pages_dir.glob("page-*.png")):
        return
    run([sys.executable, str(script_dir / "render_pdf_pages.py"), str(pdf), "--out", str(pages_dir), "--dpi", str(dpi)])


def crop_candidate_figures(script_dir: Path, pdf: Path, project: Path, figures: list[FigureCaption], max_figures: int) -> dict[str, str]:
    mapping: dict[str, str] = {}
    specs = []
    for fig in figures[:max_figures]:
        number = re.sub(r"[^0-9A-Za-z]+", "_", fig.label).strip("_").lower()
        specs.append({
            "file": f"{number}.png",
            "page": fig.page,
            "label": fig.label,
            "column": "auto",
            "position": "above",
            "padding": 16,
            "min_width": 1100,
            "min_height": 420,
        })
    for item in specs:
        tmp = project / "intermediate" / f"crop_{Path(item['file']).stem}.json"
        tmp.write_text(json.dumps([item], ensure_ascii=False, indent=2), encoding="utf-8")
        status = run([
            sys.executable,
            str(script_dir / "crop_pdf_figures_by_caption.py"),
            "--pdf",
            str(pdf),
            "--pages",
            str(project / "pages"),
            "--spec",
            str(tmp),
            "--out",
            str(project / "figures"),
        ], allow_fail=True)
        out = project / "figures" / item["file"]
        if out.exists():
            mapping[item["label"]] = f"figures/{item['file']}"
        elif status:
            (project / "intermediate" / "crop_failures.log").write_text(status + "\n", encoding="utf-8")
    return mapping


def build_paper_model(pdf: Path, pages: list[str], figures: list[FigureCaption]) -> dict:
    full_text = "\n".join(pages)
    sentences = split_sentences(full_text)
    title = extract_title(pages[0] if pages else "", pdf)
    authors = extract_authors(pages[0] if pages else "", title)
    abstract = extract_abstract(full_text)
    problem = first_matching(sentences, ["notoriously hard", "NP-hard", "traffic planning", "routing and scheduling"], 3)
    method = first_matching(sentences, ["conflict graph", "independent vertex", "configuration-conflict", "derive"], 4)
    experiment = first_matching(sentences, ["evaluate", "evaluation", "runtime", "memory", "implementation", "ILP"], 4)
    limitations = first_matching(sentences, ["future work", "limitation", "in future", "we plan", "threat"], 2)
    if not limitations:
        limitations = ["The presentation should discuss scalability limits, heuristic dependence, and how general the evaluation setting is beyond the reported experiments."]
    year = ""
    year_match = re.search(r"\b(20\d{2}|19\d{2})\b", full_text)
    if year_match:
        year = year_match.group(1)
    return {
        "title": title,
        "authors": authors,
        "year": year,
        "paper_path": str(pdf),
        "abstract": abstract,
        "research_problem": problem,
        "core_method": method,
        "experimental_evidence": experiment,
        "limitations": limitations,
        "figure_captions": [fig.__dict__ for fig in figures],
        "presentation_principles": {
            "story_order": STORY_ORDER,
            "visual_first": True,
            "one_slide_one_message": True,
            "visual_area_min": 0.4,
            "evidence_bound": True,
        },
    }


def make_paper_analysis(model: dict) -> str:
    lines = ["# Paper Analysis\n\n"]
    lines.append(f"- Title: {model['title']}\n")
    if model.get("authors"):
        lines.append(f"- Authors: {', '.join(model['authors'])}\n")
    if model.get("year"):
        lines.append(f"- Year: {model['year']}\n")
    lines.append("\n## Abstract Signal\n\n")
    lines.append(model["abstract"] + "\n\n")
    for key, label in [
        ("research_problem", "Research Problem"),
        ("core_method", "Core Method"),
        ("experimental_evidence", "Experimental Evidence"),
        ("limitations", "Limitations / Questions"),
    ]:
        lines.append(f"## {label}\n\n")
        for item in model.get(key, []) or ["needs verification"]:
            lines.append(f"- {compact(item, 320)}\n")
        lines.append("\n")
    lines.append("## Figure Candidates\n\n")
    for fig in model.get("figure_captions", []):
        lines.append(f"- {fig['label']} on page {fig['page']}: {fig['caption']}\n")
    return "".join(lines)


def image_for(label: FigureCaption | None, image_map: dict[str, str]) -> str | None:
    if not label:
        return None
    return image_map.get(label.label)


def run_understanding_engine(script_dir: Path, pdf: Path, project: Path, lang: str) -> dict:
    output = project / "intermediate" / "research_understanding.json"
    try:
        run(
            [
                sys.executable,
                str(script_dir / "build_research_understanding.py"),
                "--pdf",
                str(pdf),
                "--project",
                str(project),
                "--lang",
                lang,
            ]
        )
    except Exception as exc:
        (project / "intermediate" / "research_understanding_error.log").write_text(str(exc), encoding="utf-8")
        return {}
    if not output.exists():
        return {}
    try:
        return json.loads(output.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        (project / "intermediate" / "research_understanding_error.log").write_text(str(exc), encoding="utf-8")
        return {}


def slide(
    kind: str,
    section: str,
    phase: str,
    title: str,
    takeaway: str,
    visual: dict,
    content: str,
    bullets: list[str],
    notes: str,
    image: str | None = None,
) -> dict:
    data = {
        "kind": kind,
        "section": section,
        "story_phase": phase,
        "title": title,
        "one_message": title,
        "audience_takeaway": takeaway,
        "page_goal": takeaway,
        "visual_area_min": 0.42,
        "visual": visual,
        "content": compact(content, 260),
        "bullets": [compact(b, 95) for b in bullets[:3]],
        "notes": notes,
    }
    if image:
        data["image"] = image
    return data


def field(data: dict, key: str, default: str = "needs verification") -> str:
    value = data.get(key)
    if isinstance(value, list):
        value = value[0] if value else ""
    if isinstance(value, dict):
        value = value.get("message") or value.get("claim") or value.get("risk") or value.get("summary") or ""
    return compact(value or default, 280)


def as_list(value, limit: int = 3, default: str = "needs verification") -> list[str]:
    if isinstance(value, list):
        out = []
        for item in value:
            if isinstance(item, dict):
                item = item.get("message") or item.get("claim") or item.get("risk") or item.get("role") or item.get("key_result") or item.get("what_it_does") or item.get("limitation_signal") or item.get("detail") or item.get("name")
            if item:
                out.append(compact(str(item), 120))
            if len(out) >= limit:
                break
        return out or [default]
    if value:
        return [compact(str(value), 120)]
    return [default]


ZH_LABELS = {
    "Existing work": "现有工作",
    "This paper's gap": "本文缺口",
    "Claim": "核心主张",
    "Evidence": "支撑证据",
    "Supported": "已被支持",
    "Needs caution": "谨慎外推",
    "Input": "输入",
    "Mechanism": "机制",
    "Output": "输出",
    "Problem": "问题",
    "Challenge": "挑战",
    "Idea": "思想",
    "Method": "方法",
    "Result": "结果",
    "Takeaway": "总结",
    "Why / What / How": "为什么 / 是什么 / 怎么做",
    "Why Effective": "为什么有效",
    "How Verified": "如何验证",
    "research claim": "研究主张",
    "problem formulation / representation": "问题建模 / 表示转换",
    "method / system": "方法 / 系统机制",
    "empirical evidence": "实验证据",
    "theory / analysis": "理论 / 分析",
    "direct / partial needs reviewer verification": "支撑强度需复核",
    "support needs verification": "支撑强度需复核",
    "needs verification": "需要复核",
}

EN_LABELS = {
    "现有工作": "Existing work",
    "本文缺口": "This paper's gap",
    "核心主张": "Claim",
    "支撑证据": "Evidence",
    "已被支持": "Supported",
    "谨慎外推": "Needs caution",
    "输入": "Input",
    "机制": "Mechanism",
    "输出": "Output",
    "问题": "Problem",
    "挑战": "Challenge",
    "思想": "Idea",
    "方法": "Method",
    "结果": "Result",
    "总结": "Takeaway",
    "需要复核": "needs verification",
}

KNOWN_TERMS = [
    "configuration-conflict graph",
    "conflict graph",
    "independent vertex set",
    "traffic planning",
    "time-triggered",
    "time-sensitive networking",
    "network calculus",
    "deep reinforcement learning",
    "reinforcement learning",
    "deadline",
    "routing",
    "scheduling",
    "admission control",
    "budget allocation",
    "ILP",
    "MILP",
    "SMT",
    "SAT",
    "TAS",
    "CBS",
    "CQF",
    "CSQF",
    "TSN",
    "DetNet",
    "WAN",
    "DRL",
    "MAPPO",
]


def cjk_count(value: str) -> int:
    return len(re.findall(r"[\u4e00-\u9fff]", str(value or "")))


def ascii_count(value: str) -> int:
    return len(re.findall(r"[A-Za-z]", str(value or "")))


def needs_zh_localization(value: str) -> bool:
    text = str(value or "").strip()
    if not text:
        return False
    if text in ZH_LABELS:
        return True
    cjk = cjk_count(text)
    ascii_letters = ascii_count(text)
    if ascii_letters < 18:
        return False
    return ascii_letters > max(18, cjk * 1.4)


def extract_key_terms(value: str, limit: int = 4) -> list[str]:
    text = re.sub(r"\s+", " ", str(value or "")).strip()
    low = text.lower()
    terms: list[str] = []
    for term in KNOWN_TERMS:
        if term.lower() in low and term not in terms:
            terms.append(term)
    for token in re.findall(r"\b[A-Z][A-Z0-9-]{1,}\b", text):
        if token not in {"THE", "AND", "FOR", "WITH", "THIS", "THAT"} and token not in terms:
            terms.append(token)
    for match in re.finditer(r"\b([A-Za-z][A-Za-z0-9-]+(?:\s+[A-Za-z][A-Za-z0-9-]+){0,3})\s+(approach|algorithm|framework|model|graph|method|scheme|system)\b", text):
        phrase = compact(match.group(0), 60)
        phrase = re.sub(r"^(implementation|evaluation|comparison|proof-of-concept)\s+of\s+(the\s+)?", "", phrase, flags=re.I)
        phrase = phrase.replace("conflict- graph", "conflict-graph").replace("conflict - graph", "conflict-graph")
        if len(phrase.split()) <= 5 and " of the " not in phrase.lower() and phrase not in terms:
            terms.append(phrase)
    return terms[:limit]


def term_text(value: str, fallback: str = "核心机制") -> str:
    terms = extract_key_terms(value)
    return "、".join(terms) if terms else fallback


def localize_visible(value, lang: str, role: str = "general", limit: int = 140) -> str:
    raw = compact(value if value is not None else "", 520)
    if lang != "zh":
        if not raw:
            return ""
        if raw in EN_LABELS:
            return EN_LABELS[raw]
        if cjk_count(raw) == 0:
            return compact(raw, limit)
        terms = term_text(raw, "the core mechanism")
        if role in {"title_idea"}:
            return compact(f"Key idea: reformulate the problem around {terms}", limit)
        if role in {"contribution", "claim", "paper_move"}:
            return compact(f"Core contribution: a new modeling or mechanism around {terms}.", limit)
        if role in {"gap", "bottleneck", "limitation_signal"}:
            return compact(f"Key gap: existing methods remain limited by assumptions, complexity, or scalability around {terms}.", limit)
        if role in {"background", "context", "requirement"}:
            return compact(f"The setting requires reliable planning or decision-making around {terms}.", limit)
        if role in {"method", "mechanism", "module"}:
            return compact(f"The method connects inputs, mechanism, and outputs around {terms}.", limit)
        if role in {"experiment", "setup", "baseline", "metric"}:
            return compact(f"The experiment validates the key claim through setup, baselines, and metrics around {terms}.", limit)
        if role in {"result", "evidence"}:
            return compact(f"The reported result supports the core claim; exact values should be checked in the paper figures.", limit)
        if role in {"limitation", "risk", "boundary"}:
            return compact(f"Use caution when generalizing beyond the evaluated settings and assumptions.", limit)
        if role in {"support"}:
            return compact("The strength of this evidence should be checked against the figure and setup.", limit)
        if role in {"story"}:
            return compact(f"Storyline: an old paradigm hits a bottleneck; the paper changes the representation or mechanism and verifies it experimentally.", limit)
        return compact(f"Visible message localized to English; source text is kept in notes/source map.", limit)
    if not raw:
        return ""
    if raw in ZH_LABELS:
        return ZH_LABELS[raw]
    if not needs_zh_localization(raw):
        return compact(raw, limit)

    low = raw.lower()
    terms = term_text(raw)
    if role in {"title_idea"}:
        return compact(f"关键思想：用 {terms} 重构问题表示", limit)
    if role in {"contribution", "claim", "paper_move"}:
        return compact(f"本文核心贡献：围绕 {terms} 提出新的建模或机制，并用于解决原问题瓶颈。", limit)
    if role in {"gap", "bottleneck", "limitation_signal"}:
        if "scalab" in low:
            return compact(f"已有方法的瓶颈在于可扩展性不足，关键矛盾集中在 {terms}。", limit)
        if "hard" in low or "difficult" in low or "np-hard" in low:
            return compact(f"原问题求解困难，直接处理 {terms} 会带来较高复杂度。", limit)
        return compact(f"现有方法仍存在适用假设、复杂度或泛化边界问题，核心相关对象是 {terms}。", limit)
    if role in {"background", "context"}:
        return compact(f"研究场景要求对 {terms} 做可靠规划或决策，因此需要更清晰的建模和验证。", limit)
    if role in {"requirement"}:
        return compact(f"系统要求围绕 {terms} 满足时延、资源、可靠性或效率约束。", limit)
    if role in {"method", "mechanism", "module"}:
        if "independent vertex" in low:
            return compact(f"方法核心是把候选配置转成图结构，并搜索 independent vertex set 来获得无冲突解。", limit)
        if "conflict graph" in low:
            return compact(f"方法核心是构建 conflict graph，用图上的冲突关系替代原始约束耦合。", limit)
        return compact(f"方法通过 {terms} 构建输入-机制-输出链条，降低原问题的耦合或搜索难度。", limit)
    if role in {"experiment", "setup"}:
        return compact(f"实验围绕 {terms} 设置场景、基线和指标，用来验证核心机制是否有效。", limit)
    if role in {"baseline"}:
        return compact(f"对比对象主要包括 {terms} 等已有方法或基线。", limit)
    if role in {"metric"}:
        return compact(f"评价指标关注 {terms} 相关的效率、质量或资源消耗。", limit)
    if role in {"result", "evidence"}:
        if "outperform" in low or "faster" in low or "more memory efficient" in low:
            return compact(f"实验结果显示：本文方法相对基线更优，优势体现在效率、内存或性能指标上。", limit)
        if "reduce" in low or "lower" in low:
            return compact(f"结果表明该方法能够降低关键开销或性能指标，支撑核心 claim。", limit)
        if "increase" in low or "improve" in low or "higher" in low:
            return compact(f"结果表明该方法提升了关键指标，支撑核心 claim。", limit)
        return compact(f"实验结果为 {terms} 相关 claim 提供了支撑，但具体数值需回到图表复核。", limit)
    if role in {"limitation", "risk", "boundary"}:
        if "future work" in low or "another direction" in low:
            return compact(f"作者指出未来仍需验证：当系统模型或关键假设变化时，方法是否依然适用。", limit)
        return compact(f"需要谨慎外推：{terms} 相关结论可能受实验范围、系统假设或输入规模限制。", limit)
    if role in {"support"}:
        return compact("该证据对核心 claim 的支撑强度需要结合图表和实验设置复核。", limit)
    if role in {"story"}:
        return compact(f"故事线：旧范式遇到瓶颈，作者围绕 {terms} 改变表示或机制，并通过实验验证。", limit)
    return compact(f"核心信息围绕 {terms}；英文原文证据保留在 notes/source map 中。", limit)


def localize_list(value, lang: str, role: str = "general", limit: int = 3, item_limit: int = 110) -> list[str]:
    return [localize_visible(item, lang, role, item_limit) for item in as_list(value, limit)]


def localize_steps(steps: list[dict], lang: str, role: str = "general") -> list[dict]:
    out: list[dict] = []
    for idx, step in enumerate(steps, 1):
        label = step.get("label", f"Step {idx}")
        detail = step.get("detail", "")
        if lang == "zh":
            label = ZH_LABELS.get(str(label), str(label).replace("Module", "模块").replace("Step", "步骤"))
        out.append({
            "label": compact(label, 40),
            "detail": localize_visible(detail, lang, role, 120),
        })
    return out


def collect_visible_text(section: dict) -> list[tuple[str, str]]:
    rows: list[tuple[str, str]] = []
    for key in ["title", "one_message", "audience_takeaway", "page_goal", "content"]:
        if section.get(key):
            rows.append((key, str(section[key])))
    for idx, item in enumerate(section.get("bullets") or [], 1):
        rows.append((f"bullet_{idx}", str(item)))
    visual = section.get("visual") or {}
    for key in ["headline", "insight", "so_what", "left_title", "right_title"]:
        if visual.get(key):
            rows.append((f"visual.{key}", str(visual[key])))
    for side in ["left", "right", "items"]:
        for idx, item in enumerate(visual.get(side) or [], 1):
            rows.append((f"visual.{side}_{idx}", str(item)))
    for idx, step in enumerate(visual.get("steps") or [], 1):
        rows.append((f"visual.step_{idx}.label", str(step.get("label", ""))))
        rows.append((f"visual.step_{idx}.detail", str(step.get("detail", ""))))
    return rows


def language_issues(spec: dict) -> list[str]:
    lang = spec.get("language", "zh")
    issues: list[str] = []
    for idx, section in enumerate(spec.get("sections") or spec.get("slides") or [], 1):
        for field_name, value in collect_visible_text(section):
            if idx == 1 and field_name == "title":
                continue
            if lang == "zh":
                long_runs = re.findall(r"[A-Za-z][A-Za-z0-9 ,;:/().'\-]{90,}", value)
                if long_runs:
                    issues.append(f"Slide {idx} {field_name}: long English visible text -> {compact(long_runs[0], 120)}")
            elif lang == "en" and cjk_count(value) > 8:
                issues.append(f"Slide {idx} {field_name}: Chinese visible text in English mode -> {compact(value, 120)}")
    return issues


def write_language_report(path: Path, spec: dict) -> None:
    issues = language_issues(spec)
    lines = [
        "# Language Check Report\n\n",
        f"Target language: {spec.get('language', 'zh')}\n\n",
        f"Overall status: {'PASS' if not issues else 'WARN'}\n\n",
        "## Checks\n\n",
        "- zh: no long English prose should be visible, except paper titles and technical terms.\n",
        "- en: no Chinese template text should be visible.\n",
        "- Source-language evidence may remain in notes, source_map, or research_understanding artifacts.\n\n",
        "## Issues\n\n",
    ]
    if issues:
        lines.extend(f"- {issue}\n" for issue in issues)
    else:
        lines.append("- None\n")
    path.write_text("".join(lines), encoding="utf-8")


def module_steps(method_model: dict, limit: int = 4) -> list[dict]:
    modules = method_model.get("modules") or []
    steps: list[dict] = []
    for idx, module in enumerate(modules[:limit], 1):
        if isinstance(module, dict):
            label = module.get("name") or f"Step {idx}"
            detail = module.get("role") or module.get("detail") or module.get("claim") or ""
        else:
            label = f"Step {idx}"
            detail = str(module)
        steps.append({"label": compact(label, 40), "detail": compact(detail, 120)})
    if not steps:
        steps = [
            {"label": "Input", "detail": compact("Problem setting and constraints", 100)},
            {"label": "Mechanism", "detail": compact(method_model.get("core_mechanism", "needs verification"), 120)},
            {"label": "Output", "detail": compact("; ".join(as_list(method_model.get("outputs"), 2)), 120)},
        ]
    return steps


def build_spec_from_understanding(model: dict, understanding: dict, image_map: dict[str, str], picks: dict[str, FigureCaption | None], lang: str) -> dict:
    zh = lang == "zh"
    def text(zh_value: str, en_value: str) -> str:
        return zh_value if zh else en_value

    title = understanding.get("title") or model["title"]
    abstract = understanding.get("abstract") or model.get("abstract", "")
    domain = understanding.get("domain_primer") or {}
    motivation = understanding.get("motivation_chain") or {}
    gap = understanding.get("gap_analysis") or {}
    contributions = understanding.get("contribution_cards") or []
    method_model = understanding.get("method_model") or {}
    why = understanding.get("why_effective") or {}
    experiments = understanding.get("experiment_cards") or []
    result_matrix = understanding.get("result_to_claim_matrix") or []
    limitations = understanding.get("limitation_risks") or []
    story = understanding.get("research_story_brief") or {}

    abstract_visible = localize_visible(abstract, lang, "story", 260)
    primary_contribution_raw = field(contributions[0] if contributions else {}, "claim", motivation.get("paper_move") or abstract)
    gap_statement_raw = field(gap, "gap_statement", motivation.get("broken_assumption_or_bottleneck") or abstract)
    core_mechanism_raw = field(method_model, "core_mechanism", primary_contribution_raw)
    experiment_result_raw = field(experiments[0] if experiments else {}, "key_result", "experiment result needs verification")
    limitation_raw = field(limitations[0] if limitations else {}, "risk", "evaluation scope and assumptions need discussion")

    primary_contribution = localize_visible(primary_contribution_raw, lang, "contribution", 180)
    gap_statement = localize_visible(gap_statement_raw, lang, "gap", 180)
    core_mechanism = localize_visible(core_mechanism_raw, lang, "method", 190)
    experiment_result = localize_visible(experiment_result_raw, lang, "result", 180)
    limitation = localize_visible(limitation_raw, lang, "limitation", 180)

    background_steps = [
        {"label": text("场景压力", "Context pressure"), "detail": localize_visible(field(domain, "field_context", abstract), lang, "background", 120)},
        {"label": text("技术要求", "Technical requirement"), "detail": localize_visible(field(domain, "technical_requirement"), lang, "requirement", 120)},
        {"label": text("瓶颈出现", "Bottleneck"), "detail": localize_visible(field(domain, "planning_pressure", gap_statement_raw), lang, "gap", 120)},
    ]
    motivation_steps = [
        {"label": text("已有范式", "Existing paradigm"), "detail": localize_visible(field(motivation, "prevailing_approach"), lang, "background", 120)},
        {"label": text("失效点", "Broken assumption"), "detail": localize_visible(field(motivation, "broken_assumption_or_bottleneck", gap_statement_raw), lang, "gap", 120)},
        {"label": text("研究机会", "Research need"), "detail": localize_visible(field(motivation, "research_need"), lang, "gap", 120)},
        {"label": text("本文动作", "Paper move"), "detail": localize_visible(field(motivation, "paper_move", primary_contribution_raw), lang, "paper_move", 120)},
    ]
    why_steps = [{"label": text(f"因果 {idx}", f"Cause {idx}"), "detail": localize_visible(item, lang, "method", 130)} for idx, item in enumerate(why.get("causal_chain") or [], 1)]
    if not why_steps:
        why_steps = [
            {"label": text("瓶颈", "Bottleneck"), "detail": gap_statement},
            {"label": text("机制", "Mechanism"), "detail": core_mechanism},
            {"label": text("效果", "Effect"), "detail": experiment_result},
        ]

    result_claim_raw = result_matrix[0]["claim"] if result_matrix else primary_contribution_raw
    result_evidence_raw = result_matrix[0]["evidence"] if result_matrix else experiment_result_raw
    result_claim = localize_visible(result_claim_raw, lang, "claim", 130)
    result_evidence = localize_visible(result_evidence_raw, lang, "evidence", 130)
    experiment_setup = experiments[0] if experiments else {}
    experiment_steps = [
        {"label": text("设置", "Setup"), "detail": "；".join(localize_list(experiment_setup.get("setup"), lang, "setup", 2))},
        {"label": text("基线", "Baselines"), "detail": "；".join(localize_list(experiment_setup.get("baselines"), lang, "baseline", 2))},
        {"label": text("指标", "Metrics"), "detail": "；".join(localize_list(experiment_setup.get("metrics"), lang, "metric", 2))},
        {"label": text("结果", "Result"), "detail": experiment_result},
    ]

    sections = [
        slide(
            "cover",
            "Title",
            "Problem",
            title,
            text("先记住论文的研究故事，而不是论文目录。", "Remember the research story, not the paper table of contents."),
            {"type": "concept", "headline": localize_visible(story.get("one_sentence") or primary_contribution_raw, lang, "story", 120), "insight": text("本页只给听众建立研究对象和核心转向。", "Set up the research object and core move.")},
            abstract_visible,
            [text("Why / What / How", "Why / What / How"), text("Why Effective", "Why Effective"), text("How Verified", "How Verified")],
            "Source: title page, abstract, and Research Understanding Engine.",
        ),
        slide(
            "background",
            "Background",
            "Problem",
            text("背景不是常识铺垫，而是需求压力链", "Background is the demand-pressure chain"),
            text("观众看到：应用/系统要求如何一步步变成论文问题。", "Audience sees how application pressure becomes the paper problem."),
            {"type": "pipeline", "steps": background_steps, "insight": text("背景页必须解释为什么这个问题值得做。", "The background slide explains why the problem matters.")},
            localize_visible(field(domain, "field_context", abstract), lang, "background", 240),
            [
                localize_visible(field(domain, "technical_requirement"), lang, "requirement", 90),
                localize_visible(field(domain, "planning_pressure", gap_statement_raw), lang, "gap", 90),
            ],
            "Source: domain_primer.md and abstract/introduction.",
            image_for(picks.get("background"), image_map),
        ),
        slide(
            "problem",
            "Problem",
            "Challenge",
            text("核心矛盾：旧范式的假设撑不住本文场景", "Core tension: the old assumption breaks in this setting"),
            text("观众记住现有方法到底哪里不行。", "Audience remembers where existing methods fail."),
            {
                "type": "comparison",
                "left_title": text("现有工作", "Existing work"),
                "right_title": text("本文缺口", "This paper's gap"),
                "left": localize_list(gap.get("why_existing_is_not_enough"), lang, "limitation_signal", 3),
                "right": [gap_statement, localize_visible(field(gap, "paper_specific_opportunity"), lang, "gap", 120)],
                "insight": text("问题页用对比图，不用问题清单。", "Use contrast, not a flat problem list."),
            },
            gap_statement,
            [
                localize_visible(field(motivation, "prevailing_approach"), lang, "background", 90),
                localize_visible(field(motivation, "broken_assumption_or_bottleneck", gap_statement_raw), lang, "gap", 90),
            ],
            "Source: motivation_chain.json, related_work_matrix.json, and gap_analysis.json.",
        ),
        slide(
            "motivation",
            "Motivation",
            "Challenge",
            text("动机链：从已有范式到本文动作", "Motivation chain: from old paradigm to paper move"),
            text("观众理解作者为什么必须换一种做法。", "Audience understands why a new move is needed."),
            {"type": "flow", "steps": motivation_steps, "insight": localize_visible(field(motivation, "presentation_angle"), lang, "story", 140)},
            localize_visible(field(motivation, "research_need"), lang, "gap", 220),
            [localize_visible(field(motivation, "paper_move", primary_contribution_raw), lang, "paper_move", 100)],
            "Source: motivation_chain.json.",
        ),
        slide(
            "method",
            "Idea",
            "Idea",
            text("关键思想：用核心机制重构问题表示", "Key idea: " + compact(primary_contribution_raw, 80)),
            text("观众用一句话复述本文的核心转向。", "Audience can restate the core move in one sentence."),
            {"type": "concept", "headline": primary_contribution, "insight": text("只保留最核心贡献，避免把贡献页做成摘要页。", "Keep only the central contribution.")},
            primary_contribution,
            [localize_visible(card.get("type", "claim"), lang, "support", 80) for card in contributions[:3]] or [text("核心贡献需要复核", "Core contribution needs verification")],
            "Source: contribution_cards.json.",
            image_for(picks.get("idea"), image_map),
        ),
        slide(
            "method",
            "Method",
            "Method",
            text("方法概览：输入、机制、输出必须连成链", "Method overview: connect inputs, mechanism, and outputs"),
            text("观众 30 秒内能复述方法流程。", "Audience can retell the method flow in 30 seconds."),
            {"type": "pipeline", "steps": localize_steps(module_steps(method_model), lang, "method"), "insight": core_mechanism},
            core_mechanism,
            localize_list(method_model.get("inputs"), lang, "setup", 1) + localize_list(method_model.get("outputs"), lang, "method", 1),
            "Source: method_model.json and method section.",
            image_for(picks.get("method"), image_map),
        ),
        slide(
            "algorithm",
            "Why Effective",
            "Method",
            text("为什么有效：把瓶颈、机制、结果串起来", "Why it works: connect bottleneck, mechanism, and result"),
            text("观众知道方法不是结构堆砌，而有因果解释。", "Audience sees a causal explanation, not a component list."),
            {"type": "flow", "steps": why_steps[:4], "insight": localize_visible(field(why, "tradeoff"), lang, "method", 140)},
            localize_visible(field(why, "mechanism_summary", core_mechanism_raw), lang, "method", 240),
            [localize_visible(field(why, "tradeoff"), lang, "limitation", 110)],
            "Source: why_effective.md.",
            image_for(picks.get("idea"), image_map),
        ),
        slide(
            "experiment",
            "Experiment",
            "Result",
            text("实验设计：验证链路，而不是参数堆砌", "Experiment design: validation chain, not parameter dumping"),
            text("观众知道作者用什么设置、基线和指标验证核心 claim。", "Audience knows setup, baselines, metrics, and target claim."),
            {"type": "pipeline", "steps": experiment_steps, "insight": text("实验页要回答：它在验证哪个 claim？", "Experiment slide answers: which claim is being verified?")},
            experiment_result,
            localize_list(experiment_setup.get("metrics"), lang, "metric", 2),
            "Source: experiment_cards.json and evaluation section.",
            image_for(picks.get("experiment"), image_map),
        ),
        slide(
            "result",
            "Results",
            "Result",
            text("结果页必须回答 So What，而不是贴图", "Results must answer So What, not just show plots"),
            text("观众看到结果如何支撑核心贡献。", "Audience sees how the result supports the core claim."),
            {
                "type": "comparison",
                "left_title": text("核心主张", "Claim"),
                "right_title": text("支撑证据", "Evidence"),
                "left": [result_claim],
                "right": [result_evidence],
                "insight": text("So What：证据应直接回扣贡献。", "So What: evidence must point back to the contribution."),
                "so_what": result_evidence,
            },
            experiment_result,
            [localize_visible(row.get("support", "support needs verification"), lang, "support", 100) for row in result_matrix[:2]] or [text("证据支持强度需要复核", "Support strength needs verification")],
            "Source: result_to_claim_matrix.json.",
            image_for(picks.get("result"), image_map),
        ),
        slide(
            "closing",
            "Discussion",
            "Takeaway",
            text("讨论：哪些结论能外推，哪些不能", "Discussion: what can and cannot be generalized"),
            text("观众知道论文贡献边界，避免过度宣传。", "Audience knows the boundary of the contribution."),
            {
                "type": "comparison",
                "left_title": text("已被支持", "Supported"),
                "right_title": text("谨慎外推", "Needs caution"),
                "left": [primary_contribution, experiment_result],
                "right": localize_list(limitations, lang, "limitation", 3),
                "insight": text("老教授最关心的是 claim 和 evidence 是否匹配。", "A senior professor asks whether claims match evidence."),
            },
            limitation,
            [localize_visible(item.get("reviewer_question", ""), lang, "limitation", 110) for item in limitations[:2] if isinstance(item, dict)] or [text("审稿人问题需要补充", "Reviewer questions need follow-up")],
            "Source: limitation_risks.json and understanding_review.md.",
        ),
        slide(
            "closing",
            "Takeaways",
            "Takeaway",
            text("最后带走三件事：贡献、有效性、边界", "Take away three things: contribution, mechanism, boundary"),
            text("观众能用三句话评价这篇论文。", "Audience can evaluate the paper in three sentences."),
            {
                "type": "concept",
                "headline": text("最大贡献 / 为什么有效 / 最大局限", "Main contribution / Why effective / Main limitation"),
                "insight": localize_visible(story.get("one_sentence") or primary_contribution_raw, lang, "story", 180),
            },
            localize_visible(story.get("one_sentence") or primary_contribution_raw, lang, "story", 220),
            [
                text("贡献：", "Contribution: ") + compact(primary_contribution, 95),
                text("有效性：", "Why effective: ") + compact(core_mechanism, 95),
                text("边界：", "Boundary: ") + compact(limitation, 95),
            ],
            "Source: research_story_brief.md and understanding_review.md.",
        ),
    ]

    return {
        "title": title,
        "subtitle": "Academic Presentation Agent output: research-understanding-driven deck",
        "language": lang,
        "source_pdf": model["paper_path"],
        "understanding_engine": {
            "enabled": True,
            "artifacts": [
                "research_understanding.json",
                "motivation_chain.json",
                "gap_analysis.json",
                "contribution_cards.json",
                "method_model.json",
                "why_effective.md",
                "experiment_cards.json",
                "result_to_claim_matrix.json",
                "understanding_review.md",
            ],
        },
        "style": {
            "primary_color": "111827",
            "secondary_color": "2563EB",
            "accent_color": "DC2626",
            "neutral_color": "6B7280",
            "light_color": "F8FAFC",
            "title_font": "Microsoft YaHei",
            "body_font": "Microsoft YaHei",
            "title_size": 30,
            "body_size": 18,
            "layout": "visual-first",
            "animation": "disable",
            "design_system": "academic-agent",
        },
        "reference_design_philosophy": {
            "policy": "Learn design philosophy only; do not copy reference colors or fonts.",
            "story_order": STORY_ORDER,
            "visual_area_min": 0.4,
            "learned_patterns": [
                "one slide one message",
                "visual-first planning",
                "research-story first",
                "claim-evidence binding",
                "professor review loop",
            ],
        },
        "sections": sections,
    }


def build_spec(model: dict, image_map: dict[str, str], picks: dict[str, FigureCaption | None], lang: str) -> dict:
    understanding = model.get("research_understanding") or {}
    if understanding:
        return build_spec_from_understanding(model, understanding, image_map, picks, lang)

    title = model["title"]
    problem = model.get("research_problem") or []
    method = model.get("core_method") or []
    experiment = model.get("experimental_evidence") or []
    limitations = model.get("limitations") or []

    problem_text = compact(problem[0] if problem else model.get("abstract", ""), 420)
    method_text = compact(" ".join(method[:2]), 500)
    experiment_text = compact(" ".join(experiment[:2]), 480)
    limitation_text = compact(limitations[0] if limitations else "needs verification", 360)

    sections = [
        slide(
            "cover",
            "Title",
            "Problem",
            title,
            "这篇论文把 TT 流量规划重新表述为 conflict graph 上的独立点集搜索。",
            {"type": "concept", "headline": "Traffic planning -> conflict graph -> independent vertex set", "insight": "先让听众记住论文的建模转向，而不是直接进入公式。"},
            model.get("abstract", ""),
            ["Time-triggered traffic planning", "Conflict graph formulation", "Evaluation against ILP"],
            "Source: title page and abstract.",
        ),
        slide(
            "background",
            "Background",
            "Problem",
            "为什么 TT 流量规划是 TSN/实时网络的核心瓶颈",
            "听众理解：TAS/TT 通信需要同时确定路由和发送时刻。",
            {"type": "pipeline", "steps": [
                {"label": "Real-time flows", "detail": "周期、大小、deadline 等需求"},
                {"label": "Network topology", "detail": "交换机、链路、候选路径"},
                {"label": "TAS schedules", "detail": "每个端口的周期性发送窗口"},
            ], "insight": "背景页用任务链说明：规划阶段决定后续能否确定性传输。"},
            problem_text,
            ["TT 流依赖全网协调配置", "联合 routing + scheduling 通常 NP-hard"],
            "Source: abstract and introduction.",
            image_for(picks.get("background"), image_map),
        ),
        slide(
            "problem",
            "Problem",
            "Challenge",
            "旧问题不是缺一个约束，而是变量耦合太强",
            "听众记住：传统约束模型把单条流配置和全局网络配置绑得很紧。",
            {"type": "comparison", "left_title": "Constraint-based planning", "right_title": "Paper's target", "left": ["直接约束路径/时隙", "变量强耦合", "求解规模容易膨胀"], "right": ["先枚举可行配置", "用冲突边表达不可共存", "转为图上的独立点集"], "insight": "问题页强调建模域的变化，而不是单个算法技巧。"},
            problem_text,
            ["传统 ILP/SMT/SAT 直接在网络变量上建模", "论文指出这会影响 scalability 和 runtime"],
            "Source: abstract, introduction, and related work.",
        ),
        slide(
            "method",
            "Idea",
            "Idea",
            "核心思想：把网络规划变成 conflict graph 选择问题",
            "听众理解：每个顶点代表一个 stream configuration，冲突边代表不能同时选择。",
            {"type": "concept", "headline": "Select one feasible configuration per stream without conflicts", "insight": "如果独立点集覆盖所有 stream，原始 traffic planning 问题也被解决。"},
            method_text,
            ["顶点：候选 stream configuration", "边：配置之间存在资源/时间冲突", "解：覆盖所有流的 independent vertex set"],
            "Source: Section III and contribution paragraph.",
            image_for(picks.get("idea"), image_map),
        ),
        slide(
            "method",
            "Method",
            "Method",
            "方法概览：从候选配置到迭代式 conflict-graph planning",
            "听众能在 30 秒内复述方法流程。",
            {"type": "pipeline", "steps": [
                {"label": "Generate candidates", "detail": "为每条流生成可行 route/schedule 配置"},
                {"label": "Build conflicts", "detail": "把不可共存的配置连成冲突边"},
                {"label": "Search independent set", "detail": "选择互不冲突的一组配置"},
                {"label": "Grow graph", "detail": "不够完整时继续增加候选"},
            ], "insight": "视觉重点是 iterative CGTP，而不是把论文公式塞满页面。"},
            method_text,
            ["不必一开始构造完整解空间", "可以提前得到部分可行解"],
            "Source: introduction, Section III, and framework figures.",
            image_for(picks.get("method"), image_map),
        ),
        slide(
            "algorithm",
            "Method",
            "Method",
            "机制细节：独立点集为什么对应一个无冲突调度",
            "听众理解 conflict graph 解和原问题解之间的对应关系。",
            {"type": "flow", "steps": [
                {"label": "One vertex", "detail": "一条流的一种 route + schedule 配置"},
                {"label": "Conflict edge", "detail": "两个配置在链路或时间上冲突"},
                {"label": "Independent set", "detail": "被选配置之间没有冲突"},
                {"label": "Complete coverage", "detail": "每条流都有一个被选配置"},
            ], "insight": "这个对应关系是论文最重要的理论直觉。"},
            method_text,
            ["图论对象替代原始约束空间", "完整 independent set 即完整规划解"],
            "Source: Section III figures and problem formulation.",
            image_for(picks.get("idea"), image_map),
        ),
        slide(
            "experiment",
            "Experiment",
            "Result",
            "实验验证链路：先证明可实现，再比较 ILP 基线",
            "听众知道实验不是参数堆砌，而是在验证建模转向是否带来 runtime/memory 优势。",
            {"type": "pipeline", "steps": [
                {"label": "Implementation", "detail": "proof-of-concept CGTP"},
                {"label": "Baseline", "detail": "reference ILP implementation"},
                {"label": "Metrics", "detail": "runtime and memory efficiency"},
                {"label": "Scales", "detail": "problem size and stream/node ratio"},
            ], "insight": "实验页用验证链路组织，而不是逐图截图。"},
            experiment_text,
            ["比较对象：constraint-based ILP", "指标聚焦求解时间和内存"],
            "Source: abstract, contribution paragraph, and evaluation section.",
            image_for(picks.get("experiment"), image_map),
        ),
        slide(
            "result",
            "Results",
            "Result",
            "主要结果：CGTP 在求解效率上优于参考 ILP",
            "听众记住 So What：conflict-graph formulation 不只是概念优雅，也改善规划阶段效率。",
            {"type": "concept", "headline": "CGTP outperforms reference ILP in reported evaluations", "insight": "So What: 更快、更省内存的规划阶段，让 TT 配置更接近动态网络需求。"},
            experiment_text,
            ["论文报告 proof-of-concept 超过参考 ILP", "内存效率更好", "结果支持 conflict graph 作为替代建模方向"],
            "Source: abstract and evaluation section. Do not infer exact percentages unless extracted from the paper.",
            image_for(picks.get("result"), image_map),
        ),
        slide(
            "result",
            "Discussion",
            "Result",
            "为什么这个结果有意义：它降低的是规划阶段的耦合成本",
            "听众理解贡献不是一个更快的 solver，而是改变了问题表示方式。",
            {"type": "comparison", "left_title": "If staying in constraint domain", "right_title": "After conflict graph reformulation", "left": ["变量多且相互约束", "难以逐步扩展解空间", "早停时难得到有用部分解"], "right": ["候选配置可逐步加入", "独立点集给出可解释解", "可支持部分流的提前可行解"], "insight": "这页把结果和方法思想重新连起来。"},
            method_text,
            ["建模转向带来可扩展空间", "动态场景下部分解也可能有价值"],
            "Source: introduction discussion on partial solutions and dynamic scenarios.",
        ),
        slide(
            "closing",
            "Takeaways",
            "Takeaway",
            "Takeaways：最大贡献、最大创新、最大局限",
            "听众带走三个判断：问题重表述、图论求解、评估范围仍需追问。",
            {"type": "concept", "headline": "Contribution: conflict-graph formulation for TT traffic planning", "insight": "Novelty: independent vertex set view. Limitation: proof-of-concept and evaluation scope should be discussed."},
            limitation_text,
            ["最大贡献：把 TT 规划转成 conflict graph", "最大创新：独立点集对应无冲突配置集", "最大局限：泛化场景和大规模部署仍需追问"],
            "Source: contribution paragraph, conclusion, and conservative reviewer perspective.",
        ),
    ]

    return {
        "title": title,
        "subtitle": "Academic Presentation Agent output: visual-first group meeting deck",
        "language": lang,
        "source_pdf": model["paper_path"],
        "style": {
            "primary_color": "111827",
            "secondary_color": "2563EB",
            "accent_color": "DC2626",
            "neutral_color": "6B7280",
            "light_color": "F8FAFC",
            "title_font": "Microsoft YaHei",
            "body_font": "Microsoft YaHei",
            "title_size": 30,
            "body_size": 18,
            "layout": "visual-first",
            "animation": "disable",
            "design_system": "academic-agent",
        },
        "reference_design_philosophy": {
            "policy": "Learn design philosophy only; do not copy reference colors or fonts.",
            "story_order": STORY_ORDER,
            "visual_area_min": 0.4,
            "learned_patterns": [
                "one slide one message",
                "visual-first planning",
                "visual-text zoning",
                "disciplined whitespace",
                "stable academic frame",
                "professor review loop",
            ],
        },
        "sections": sections,
    }


def write_story_artifacts(project: Path, model: dict, spec: dict) -> None:
    intermediate = project / "intermediate"
    (intermediate / "paper_model.json").write_text(json.dumps(model, ensure_ascii=False, indent=2), encoding="utf-8")
    (intermediate / "paper_analysis.md").write_text(make_paper_analysis(model), encoding="utf-8")

    storyboard = []
    visual_plan = []
    outline = ["# Slide Outline\n\n"]
    source_map = ["# Source Map\n\n"]
    for idx, sec in enumerate(spec["sections"], 1):
        outline.append(f"{idx}. [{sec['story_phase']}] {sec['title']}\n")
        storyboard.extend([
            f"## Slide {idx}: {sec['title']}\n\n",
            f"- Story Phase: {sec['story_phase']}\n",
            f"- One Message: {sec['one_message']}\n",
            f"- Page Goal: {sec['page_goal']}\n",
            f"- Visual: {(sec.get('visual') or {}).get('type', 'image')}\n",
            f"- Content: {sec.get('content', '')}\n\n",
        ])
        visual_plan.append({
            "slide": idx,
            "story_phase": sec["story_phase"],
            "page_goal": sec["page_goal"],
            "visual_subject": sec.get("image") or (sec.get("visual") or {}).get("headline") or (sec.get("visual") or {}).get("insight"),
            "visual_type": (sec.get("visual") or {}).get("type", "image"),
            "visual_area_min": sec.get("visual_area_min", 0.4),
            "five_second_takeaway": sec["audience_takeaway"],
        })
        source_map.append(f"## Slide {idx}: {sec['title']}\n\n")
        source_map.append(f"- Notes: {sec.get('notes', '')}\n")
        if sec.get("image"):
            source_map.append(f"- Visual evidence: {sec['image']}\n")
        source_map.append("\n")
    (intermediate / "slide_outline.md").write_text("".join(outline), encoding="utf-8")
    (intermediate / "visual_storyboard.md").write_text("".join(storyboard), encoding="utf-8")
    (intermediate / "visual_plan.json").write_text(json.dumps(visual_plan, ensure_ascii=False, indent=2), encoding="utf-8")
    (intermediate / "storyboard.json").write_text(json.dumps({"slides": spec["sections"]}, ensure_ascii=False, indent=2), encoding="utf-8")
    (intermediate / "deck_model.json").write_text(json.dumps(spec, ensure_ascii=False, indent=2), encoding="utf-8")
    (intermediate / "source_map.md").write_text("".join(source_map), encoding="utf-8")
    write_language_report(intermediate / "language_check_report.md", spec)


def write_figures_index(project: Path, figures: list[FigureCaption], image_map: dict[str, str]) -> None:
    lines = ["# Figures Index\n\n"]
    for fig in figures:
        crop = image_map.get(fig.label, "not cropped")
        lines.extend([
            f"## {fig.label}\n\n",
            f"- Source page: {fig.page}\n",
            f"- Caption: {fig.caption}\n",
            f"- Crop file: {crop}\n",
            "- Why it matters: candidate visual evidence for explaining the paper.\n",
            "- How to explain: show the visual first, then connect it to the slide's one message.\n\n",
        ])
    (project / "intermediate" / "figures_index.md").write_text("".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="One-command Academic Presentation Agent: PDF -> paper model -> story -> visual plan -> HTML + editable PPTX.")
    parser.add_argument("--pdf", type=Path, required=True)
    parser.add_argument("--project", type=Path, required=True)
    parser.add_argument("--lang", choices=["zh", "en"], default="zh")
    parser.add_argument("--dpi", type=int, default=240)
    parser.add_argument("--max-figures", type=int, default=10)
    parser.add_argument("--rounds", type=int, default=3)
    parser.add_argument("--target-score", type=float, default=9.0)
    args = parser.parse_args()

    script_dir = Path(__file__).resolve().parent
    original_pdf = args.pdf.resolve()
    project = args.project.resolve()
    pdf = ensure_project(original_pdf, project)

    pages = extract_pages(pdf)
    figures = extract_figure_captions(pages)
    model = build_paper_model(pdf, pages, figures)
    understanding = run_understanding_engine(script_dir, pdf, project, args.lang)
    if understanding:
        model["research_understanding"] = understanding

    picks = choose_figures(figures)
    selected_figures: list[FigureCaption] = []
    seen_labels = set()
    for fig in picks.values():
        if fig and fig.label not in seen_labels:
            selected_figures.append(fig)
            seen_labels.add(fig.label)
    render_pages(script_dir, pdf, project, args.dpi)
    image_map = crop_candidate_figures(script_dir, pdf, project, selected_figures[: args.max_figures], args.max_figures)
    write_figures_index(project, figures, image_map)

    spec = build_spec(model, image_map, picks, args.lang)
    intermediate = project / "intermediate"
    write_story_artifacts(project, model, spec)
    (intermediate / "slide_specs.json").write_text(json.dumps(spec, ensure_ascii=False, indent=2), encoding="utf-8")
    language_report = intermediate / "language_check_report.md"
    if language_report.exists():
        shutil.copy2(language_report, project / "language_check_report.md")

    run([
        sys.executable,
        str(script_dir / "refine_presentation_loop.py"),
        "--project",
        str(project),
        "--rounds",
        str(args.rounds),
        "--target-score",
        str(args.target_score),
    ])
    if language_report.exists() and (project / "final").exists():
        shutil.copy2(language_report, project / "final" / "language_check_report.md")
    print(project / "final" / "final_presentation_generated.pptx")
    print(project / "final" / "final_presentation_generated.html")


if __name__ == "__main__":
    main()
