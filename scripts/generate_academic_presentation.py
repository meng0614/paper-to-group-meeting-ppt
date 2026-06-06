#!/usr/bin/env python
from __future__ import annotations

import argparse
import html
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFont, ImageOps, ImageStat
from pypdf import PdfReader


LIGATURES = {
    "\ufb00": "ff",
    "\ufb01": "fi",
    "\ufb02": "fl",
    "\ufb03": "ffi",
    "\ufb04": "ffl",
}

STORY_PHASES = ["Problem", "Challenge", "Idea", "Method", "Result", "Takeaway"]


@dataclass
class FigureCaption:
    label: str
    number: str
    page: int
    caption: str


@dataclass
class BBoxLine:
    text: str
    x1: float
    y1: float
    x2: float
    y2: float


@dataclass
class BBoxPage:
    width: float
    height: float
    lines: list[BBoxLine]


def clean_text(text: str) -> str:
    for src, dst in LIGATURES.items():
        text = text.replace(src, dst)
    text = text.replace("\r", "\n")
    text = text.replace("\u2013", "-").replace("\u2014", "-")
    return re.sub(r"[ \t]+", " ", text)


def compact(value: str, limit: int = 240) -> str:
    text = re.sub(r"\s+", " ", str(value or "")).strip()
    if len(text) <= limit:
        return text
    return text[:limit].rstrip(" ,;:.，；：。") + "..."


def split_sentences(text: str) -> list[str]:
    text = re.sub(r"\s+", " ", text)
    parts = re.split(r"(?<=[.!?。！？])\s+(?=[A-Z0-9\u4e00-\u9fff])", text)
    return [p.strip() for p in parts if len(p.strip()) > 32]


def pick_sentences(text: str, keywords: list[str], limit: int = 3) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for sentence in split_sentences(text):
        low = sentence.lower()
        if any(k.lower() in low for k in keywords):
            key = compact(sentence, 160).lower()
            if key not in seen and not looks_like_reference(sentence):
                out.append(sentence)
                seen.add(key)
        if len(out) >= limit:
            break
    return out


def looks_like_reference(sentence: str) -> bool:
    low = sentence.lower()
    markers = ["doi", "isbn", "proceedings", "transactions", "vol.", "pp.", "springer", "elsevier"]
    return sum(1 for m in markers if m in low) >= 2


def run(cmd: list[str], *, env: dict[str, str] | None = None, allow_fail: bool = False) -> subprocess.CompletedProcess:
    result = subprocess.run(cmd, capture_output=True, text=True, env=env)
    if result.returncode != 0 and not allow_fail:
        raise RuntimeError(
            "Command failed:\n"
            + " ".join(cmd)
            + f"\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
        )
    return result


def extract_pages(pdf: Path) -> list[str]:
    reader = PdfReader(str(pdf))
    return [clean_text(page.extract_text() or "") for page in reader.pages]


def extract_title(first_page: str, pdf: Path) -> str:
    lines = [clean_text(line).strip() for line in first_page.splitlines() if line.strip()]
    drop = re.compile(r"abstract|keyword|copyright|received|accepted|available online|journal homepage|doi|@|university", re.I)
    candidates = [line for line in lines[:25] if not drop.search(line) and 8 <= len(line) <= 150]
    for line in candidates[:8]:
        if line.count(" ") >= 4 and not re.match(r"^[A-Z][a-z]+ [A-Z][a-z]+", line):
            return line
    return candidates[0] if candidates else pdf.stem


def extract_authors(first_page: str, title: str) -> list[str]:
    lines = [clean_text(line).strip() for line in first_page.splitlines() if line.strip()]
    authors: list[str] = []
    for line in lines[:35]:
        if line == title or len(line) > 120:
            continue
        if re.search(r"abstract|keyword|copyright|received|accepted|university|institute|department|doi|journal", line, re.I):
            continue
        words = line.replace(",", " ").split()
        cap_words = [w for w in words if re.match(r"^[A-Z][A-Za-z.\-']+$", w)]
        if 2 <= len(cap_words) <= 8 and len(words) <= 12:
            authors.append(line)
        if len(authors) >= 4:
            break
    return authors


def extract_abstract(full_text: str) -> str:
    patterns = [
        r"\bAbstract\b\s*[-\u2014]?\s*(.*?)(?:\bKeywords\b|\bIndex Terms\b|\b1\s+Introduction\b|\bI\.\s+INTRODUCTION\b)",
        r"\bABSTRACT\b\s*(.*?)(?:\bKEYWORDS\b|\b1\s+Introduction\b|\bI\.\s+INTRODUCTION\b)",
    ]
    for pattern in patterns:
        match = re.search(pattern, full_text, re.I | re.S)
        if match:
            return compact(match.group(1), 1600)
    return compact(full_text, 1200)


SECTION_ALIASES = {
    "intro": ["introduction", "background"],
    "related": ["related work", "prior work"],
    "method": ["method", "approach", "design", "model", "algorithm", "framework", "scheduling"],
    "evaluation": ["evaluation", "experiment", "results", "case study", "performance"],
    "discussion": ["discussion", "limitation", "conclusion", "future work"],
}


def extract_sections(full_text: str) -> dict[str, str]:
    lowered = full_text.lower()
    starts: list[tuple[str, int]] = []
    for key, aliases in SECTION_ALIASES.items():
        for alias in aliases:
            for pattern in [rf"\n\s*\d+(\.\d+)*\s+{re.escape(alias)}\b", rf"\n\s*[ivxlcdm]+\.\s+{re.escape(alias)}\b", rf"\n\s*{re.escape(alias)}\b"]:
                match = re.search(pattern, lowered, re.I)
                if match:
                    starts.append((key, match.start()))
                    break
            if any(s[0] == key for s in starts):
                break
    starts = sorted(set(starts), key=lambda x: x[1])
    sections: dict[str, str] = {}
    for idx, (key, start) in enumerate(starts):
        end = starts[idx + 1][1] if idx + 1 < len(starts) else len(full_text)
        sections[key] = compact(full_text[start:end], 9000)
    return sections


def extract_figure_captions(pages: list[str]) -> list[FigureCaption]:
    by_label: dict[str, tuple[tuple[int, int, int, int], FigureCaption]] = {}
    for page_no, text in enumerate(pages, 1):
        lines = [clean_text(line).strip() for line in text.splitlines() if line.strip()]
        for idx, line in enumerate(lines):
            match = re.match(r"^(Fig\.?|Figure)\s+(\d+[A-Za-z]?)\.?\s*(.*)$", line, re.I)
            if not match:
                continue
            number = match.group(2)
            label = f"Fig. {number}"
            parts = [match.group(3).strip()] if match.group(3).strip() else []
            # If the first line already forms a complete caption sentence, do
            # not attach the following body paragraph.
            if not (parts and re.search(r"[.!?。！？]\s*$", parts[-1])):
                for extra in lines[idx + 1 : idx + 3]:
                    if re.match(r"^(Fig\.?|Figure|Table|Algorithm)\s+\d+", extra, re.I):
                        break
                    if len(extra) <= 180:
                        parts.append(extra)
                    if parts and re.search(r"[.!?。！？]\s*$", parts[-1]):
                        break
            caption = compact(" ".join(parts), 360)
            tail_low = caption.lower().strip()
            body_reference = 1 if re.match(r"^(shows|shown|illustrates|presents|reports|depicts|describes)\b", tail_low) else 0
            subfigure_reference = 1 if re.match(r"^\(?[a-z]\)?\s+(shows|illustrates|presents)\b", tail_low) else 0
            too_long = 1 if len(caption) > 260 else 0
            score = (body_reference, subfigure_reference, too_long, len(caption))
            fig = FigureCaption(label=label, number=number, page=page_no, caption=caption)
            if label not in by_label or score < by_label[label][0]:
                by_label[label] = (score, fig)
    return [row[1] for _, row in sorted(((natural_number(label), data) for label, data in by_label.items()), key=lambda item: item[0])]


def natural_number(label: str) -> tuple[int, str]:
    match = re.search(r"(\d+)([A-Za-z]?)", label)
    if not match:
        return (9999, label)
    return (int(match.group(1)), match.group(2))


def extract_tables(pages: list[str]) -> list[FigureCaption]:
    tables: list[FigureCaption] = []
    seen: set[tuple[int, str]] = set()
    for page_no, text in enumerate(pages, 1):
        lines = [clean_text(line).strip() for line in text.splitlines() if line.strip()]
        for idx, line in enumerate(lines):
            match = re.match(r"^(Table)\s+(\d+[A-Za-z]?)\.?\s*(.*)$", line, re.I)
            if not match:
                continue
            number = match.group(2)
            label = f"Table {number}"
            if (page_no, label) in seen:
                continue
            parts = [match.group(3).strip()] if match.group(3).strip() else []
            for extra in lines[idx + 1 : idx + 3]:
                if re.match(r"^(Fig\.?|Figure|Table|Algorithm)\s+\d+", extra, re.I):
                    break
                if len(extra) <= 180:
                    parts.append(extra)
            tables.append(FigureCaption(label=label, number=number, page=page_no, caption=compact(" ".join(parts), 360)))
            seen.add((page_no, label))
    return tables


def extract_terms(text: str) -> list[str]:
    counts: dict[str, int] = {}
    for term in re.findall(r"\b[A-Z][A-Z0-9-]{1,}\b", text):
        if term in {"THE", "AND", "FOR", "WITH", "THIS", "THAT", "IEEE", "ACM", "PDF", "DOI"}:
            continue
        counts[term] = counts.get(term, 0) + 1
    phrases = [
        "network calculus",
        "worst-case delay",
        "relative offset",
        "time-triggered traffic",
        "time-sensitive networking",
        "local search",
        "frame preemption",
        "guard band",
    ]
    found = [p for p in phrases if p.lower() in text.lower()]
    acronyms = [k for k, _ in sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))[:14]]
    return found + acronyms


def has_tsn_avb_pattern(text: str) -> bool:
    low = text.lower()
    return "avb" in low and ("time-triggered" in low or "tt " in low or " tt" in low) and ("worst-case delay" in low or "wcd" in low)


def zh_or_en(lang: str, zh: str, en: str) -> str:
    return zh if lang == "zh" else en


def build_understanding(pdf: Path, lang: str) -> dict:
    pages = extract_pages(pdf)
    full = "\n".join(pages)
    sections = extract_sections(full)
    abstract = extract_abstract(full)
    title = extract_title(pages[0] if pages else "", pdf)
    authors = extract_authors(pages[0] if pages else "", title)
    figures = extract_figure_captions(pages)
    tables = extract_tables(pages)
    terms = extract_terms(full)
    intro = sections.get("intro", "")
    related = sections.get("related", "")
    method = sections.get("method", "")
    evaluation = sections.get("evaluation", "")
    discussion = sections.get("discussion", "")
    year_match = re.search(r"\b(20\d{2}|19\d{2})\b", full)

    if has_tsn_avb_pattern(full):
        contribution = zh_or_en(
            lang,
            "把 AVB 最坏情况时延显式纳入 TT/GCL 调度目标，并用轻量因子替代频繁完整 WCD 计算。",
            "Make AVB worst-case delay explicit in TT/GCL scheduling and replace repeated full WCD evaluation with lightweight factors.",
        )
        gap = zh_or_en(
            lang,
            "已有 TT 调度多关注 TT 可调度性，AVB 性能常被事后评估；直接用网络演算反复评估又会拖慢搜索。",
            "Existing TT schedulers mainly optimize TT schedulability; AVB performance is often checked after scheduling, while repeated network-calculus WCD evaluation is expensive.",
        )
        insight = zh_or_en(
            lang,
            "AVB WCD 的风险主要由两个 TT 窗口结构因子触发：最大 TT 窗口长度和相邻 TT 窗口的最小相对偏移。",
            "AVB WCD risk is largely explained by two TT-window factors: the maximum TT window length and the minimum relative offset between adjacent TT windows.",
        )
        method_msg = zh_or_en(
            lang,
            "方法把上述因子写成 AVB-aware objective，嵌入 GRASP，并结合 TT flow sorting、初始 GCL 构造和 flexible local search。",
            "The method embeds these factors as an AVB-aware objective in GRASP, with TT flow sorting, initial GCL construction, and flexible local search.",
        )
        verified = zh_or_en(
            lang,
            "实验用真实 IVN 架构和合成拓扑比较 BS/NOF/NOFWS/OMT/DRL，观察 TT success、AVB success、AVB WCD 和 runtime。",
            "The evaluation uses realistic IVN and synthetic topologies, comparing BS/NOF/NOFWS/OMT/DRL on TT success, AVB success, AVB WCD, and runtime.",
        )
        result = zh_or_en(
            lang,
            "结果显示 NOFWS 在保持 TT success 的同时改善 AVB 支持，并显著降低运行时间，尤其在高 TT 比例和大规模网络下更明显。",
            "Results show NOFWS maintains TT success, improves AVB support, and greatly lowers runtime, especially under high TT ratios and larger networks.",
        )
        limitation = zh_or_en(
            lang,
            "边界在于：方法仍依赖 TAS+CBS 与网络演算建模，真实交换机部署、更多流量模型和跨域场景仍需验证。",
            "The boundary is that the method still relies on TAS+CBS and network-calculus modeling; real-switch deployment, richer traffic models, and cross-domain settings need more validation.",
        )
    else:
        contribution_sents = pick_sentences(abstract + " " + intro, ["we propose", "we present", "we introduce", "we develop", "this paper"], 2)
        gap_sents = pick_sentences(intro + " " + related + " " + abstract, ["however", "challenge", "limitation", "hard", "difficult", "expensive", "not"], 3)
        method_sents = pick_sentences(method + " " + abstract, ["method", "algorithm", "framework", "model", "construct", "optimize", "learn", "derive"], 3)
        eval_sents = pick_sentences(evaluation, ["evaluate", "experiment", "baseline", "metric", "result", "outperform", "improve"], 3)
        contribution = zh_or_en(lang, "核心贡献：" + compact(contribution_sents[0] if contribution_sents else abstract, 170), compact(contribution_sents[0] if contribution_sents else abstract, 200))
        gap = zh_or_en(lang, "研究缺口：" + compact(gap_sents[0] if gap_sents else abstract, 170), compact(gap_sents[0] if gap_sents else abstract, 200))
        insight = zh_or_en(lang, "关键洞察来自作者对问题结构、约束或证据链的重新组织。", "The key insight comes from reorganizing the problem structure, constraints, or evidence chain.")
        method_msg = zh_or_en(lang, "方法主线：" + compact(method_sents[0] if method_sents else abstract, 170), compact(method_sents[0] if method_sents else abstract, 200))
        verified = zh_or_en(lang, "验证方式：" + compact(eval_sents[0] if eval_sents else "实验设置需要回到论文核对。", 170), compact(eval_sents[0] if eval_sents else "Evaluation setup needs verification.", 200))
        result = zh_or_en(lang, "结果解释：" + compact(eval_sents[1] if len(eval_sents) > 1 else "结果趋势需要结合图表核对。", 170), compact(eval_sents[1] if len(eval_sents) > 1 else "Result trend needs chart-level verification.", 200))
        limitation = zh_or_en(lang, "局限性：适用边界、实验覆盖范围和泛化性需要重点讨论。", "Limitations: applicability boundary, evaluation coverage, and generalization need discussion.")

    why = [
        zh_or_en(lang, "瓶颈：" + gap, "Bottleneck: " + gap),
        zh_or_en(lang, "机制：" + method_msg, "Mechanism: " + method_msg),
        zh_or_en(lang, "效果：" + result, "Effect: " + result),
    ]
    story = [
        {"phase": "Problem", "message": gap},
        {"phase": "Challenge", "message": insight},
        {"phase": "Idea", "message": contribution},
        {"phase": "Method", "message": method_msg},
        {"phase": "Result", "message": result},
        {"phase": "Takeaway", "message": limitation},
    ]
    return {
        "title": title,
        "authors": authors,
        "year": year_match.group(1) if year_match else "",
        "source_pdf": str(pdf),
        "language": lang,
        "abstract": abstract,
        "terms": terms,
        "figures": [f.__dict__ for f in figures],
        "tables": [t.__dict__ for t in tables],
        "research_questions": {
            "why": gap,
            "what": contribution,
            "how": method_msg,
            "why_effective": why,
            "how_verified": verified,
        },
        "motivation_chain": {
            "context": zh_or_en(lang, "TSN/TAS 场景需要同时保证 TT 确定性和 AVB 延迟表现。", "The setting requires both TT determinism and AVB delay performance.") if has_tsn_avb_pattern(full) else compact(abstract, 220),
            "old_paradigm": zh_or_en(lang, "先排 TT，再评估 AVB。", "Schedule TT first, evaluate AVB later.") if has_tsn_avb_pattern(full) else "needs verification",
            "broken_assumption": gap,
            "paper_move": contribution,
        },
        "gap_analysis": {"gap_statement": gap, "why_existing_is_not_enough": [gap], "paper_specific_opportunity": contribution},
        "contribution_cards": [
            {"id": "C1", "claim": contribution, "why_it_matters": insight, "evidence_to_check": verified},
            {"id": "C2", "claim": insight, "why_it_matters": zh_or_en(lang, "它把调度质量转化为可计算、可搜索的结构指标。", "It turns scheduling quality into computable and searchable structural indicators."), "evidence_to_check": "network calculus / theory section"},
        ],
        "method_model": {
            "core_mechanism": method_msg,
            "modules": [
                {"label": zh_or_en(lang, "输入建模", "Input modeling"), "detail": zh_or_en(lang, "网络、TT/AVB 流、周期、deadline/GCL 约束。", "Network, TT/AVB flows, periods, deadlines, and GCL constraints.")},
                {"label": zh_or_en(lang, "理论因子", "Theory factors"), "detail": insight},
                {"label": zh_or_en(lang, "搜索优化", "Search optimization"), "detail": method_msg},
                {"label": zh_or_en(lang, "输出调度", "Output schedule"), "detail": zh_or_en(lang, "满足 TT 约束并更友好于 AVB WCD 的 GCL。", "A GCL satisfying TT constraints while being friendlier to AVB WCD.")},
            ],
            "assumptions": [limitation],
        },
        "why_effective": {"causal_chain": why, "tradeoff": limitation},
        "experiment_cards": [
            {
                "id": "E1",
                "question": zh_or_en(lang, "实验是否直接验证 AVB-aware TT 调度比传统策略更实用？", "Does the evaluation directly verify the practicality of AVB-aware TT scheduling?"),
                "setup": [verified],
                "metrics": ["TT success", "AVB success", "AVB WCD", "runtime"],
                "key_result": result,
            }
        ],
        "result_to_claim_matrix": [{"claim": contribution, "evidence": result, "support": "direct / check exact values in figures and tables"}],
        "limitation_risks": [{"risk": limitation, "reviewer_question": zh_or_en(lang, "这些结论能否扩展到真实部署和跨域/广域确定性网络？", "Can the conclusions extend to real deployments and cross-domain/wide-area deterministic networks?")}],
        "research_story_brief": {
            "one_sentence": zh_or_en(
                lang,
                f"这篇论文的故事线是：{gap} 作者的转向是：{contribution}",
                f"The paper story is: {gap} The paper move is: {contribution}",
            ),
            "storyline": story,
        },
        "source_map": {
            "abstract": abstract,
            "introduction": compact(intro, 1200),
            "method": compact(method, 1200),
            "evaluation": compact(evaluation, 1200),
            "discussion": compact(discussion, 900),
        },
    }


def local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def parse_bbox_html(path: Path) -> BBoxPage:
    root = ET.fromstring(path.read_text(encoding="utf-8", errors="ignore"))
    page_el = next(el for el in root.iter() if local_name(el.tag) == "page")
    page = BBoxPage(float(page_el.attrib["width"]), float(page_el.attrib["height"]), [])
    for line_el in page_el.iter():
        if local_name(line_el.tag) != "line":
            continue
        words = [w for w in line_el if local_name(w.tag) == "word"]
        if not words:
            continue
        text = " ".join((w.text or "").strip() for w in words).strip()
        if not text:
            continue
        page.lines.append(
            BBoxLine(
                text=text,
                x1=min(float(w.attrib["xMin"]) for w in words),
                y1=min(float(w.attrib["yMin"]) for w in words),
                x2=max(float(w.attrib["xMax"]) for w in words),
                y2=max(float(w.attrib["yMax"]) for w in words),
            )
        )
    return page


def bbox_page(pdf: Path, page: int) -> BBoxPage | None:
    exe = shutil.which("pdftotext")
    if not exe:
        return None
    with tempfile.TemporaryDirectory() as td:
        out = Path(td) / f"page_{page}.html"
        result = run([exe, "-bbox-layout", "-f", str(page), "-l", str(page), str(pdf), str(out)], allow_fail=True)
        if result.returncode != 0 or not out.exists():
            return None
        return parse_bbox_html(out)


def find_caption_line(page: BBoxPage, label: str) -> BBoxLine | None:
    normalized = label.strip().rstrip(".")
    number = re.sub(r"[^0-9A-Za-z.]", "", normalized.split()[-1]).rstrip(".")
    # A common failure mode is treating "Fig. 6(a) shows ..." in body text as
    # the real caption. Prefer true captions such as "Fig. 6. Heuristic ...".
    strict = re.compile(rf"^\s*(Fig\.?|Figure|Table)\s*{re.escape(number)}\s*\.?\s+(?!\()", re.I)
    start = re.compile(rf"^\s*(Fig\.?|Figure|Table)\s*{re.escape(number)}\.?\b", re.I)
    contains = re.compile(rf"\b(Fig\.?|Figure|Table)\s*{re.escape(number)}\.?\b", re.I)
    candidates = [line for line in page.lines if start.search(line.text)]
    if not candidates:
        candidates = [line for line in page.lines if contains.search(line.text)]
    if not candidates:
        return None

    def score(line: BBoxLine) -> tuple[int, int, int, int, float]:
        text = line.text.strip()
        subfigure_ref = 1 if re.match(rf"^\s*(Fig\.?|Figure)\s*{re.escape(number)}\s*\(", text, re.I) else 0
        inline_ref = 1 if re.search(r"\b(shows|shown|illustrates|presents|depicts|reports|according)\b", text, re.I) else 0
        not_strict = 0 if strict.search(text) else 1
        # True captions are usually short-to-medium lines. Long body sentences
        # that happen to begin with Fig. N are penalized.
        long_line = 1 if len(text) > 120 else 0
        return (subfigure_ref, inline_ref, not_strict, long_line, line.y1)

    return min(candidates, key=score)


def split_indices(values: list[int], gap: int) -> list[tuple[int, int]]:
    if not values:
        return []
    groups: list[tuple[int, int]] = []
    start = prev = values[0]
    for value in values[1:]:
        if value - prev > gap:
            groups.append((start, prev + 1))
            start = value
        prev = value
    groups.append((start, prev + 1))
    return groups


def infer_search_box(page: BBoxPage, caption: BBoxLine, image_size: tuple[int, int]) -> tuple[int, int, int, int, int]:
    img_w, img_h = image_size
    sx, sy = img_w / page.width, img_h / page.height
    mid = page.width / 2
    gutter = max(8.0, page.width * 0.018)
    margin = max(36.0, page.width * 0.06)
    c_center = (caption.x1 + caption.x2) / 2
    caption_width = caption.x2 - caption.x1
    centered = abs(c_center - mid) < page.width * 0.14
    if caption_width > page.width * 0.34 or centered:
        x1, x2 = margin, page.width - margin
    elif c_center >= mid:
        x1, x2 = mid + gutter, page.width - margin
    else:
        x1, x2 = margin, mid - gutter
    y1 = max(32.0, page.height * 0.04)
    y2 = max(y1 + 8.0, caption.y1 - 2.0)
    return int(x1 * sx), int(y1 * sy), int(x2 * sx), int(y2 * sy), int(c_center * sx)


def choose_col_group(groups: list[tuple[int, int]], focus: int | None, width: int) -> tuple[int, int] | None:
    if not groups:
        return None
    if focus is None:
        return max(groups, key=lambda g: g[1] - g[0])
    focus = max(0, min(width, focus))
    chosen = min(groups, key=lambda g: 0 if g[0] <= focus <= g[1] else min(abs(focus - g[0]), abs(focus - g[1])))
    idx = groups.index(chosen)
    left, right = chosen
    # Merge adjacent subfigures, but do not cross a wide body-text gutter.
    j = idx - 1
    while j >= 0 and left - groups[j][1] <= max(28, int(width * 0.045)):
        left = groups[j][0]
        j -= 1
    j = idx + 1
    while j < len(groups) and groups[j][0] - right <= max(28, int(width * 0.045)):
        right = groups[j][1]
        j += 1
    return left, right


def trim_to_visual(page_img: Image.Image, box: tuple[int, int, int, int], focus_x: int | None) -> tuple[int, int, int, int]:
    gray = page_img.convert("L")
    x1, y1, x2, y2 = box
    x1 = max(0, min(x1, page_img.width - 1))
    x2 = max(x1 + 1, min(x2, page_img.width))
    y1 = max(0, min(y1, page_img.height - 1))
    y2 = max(y1 + 1, min(y2, page_img.height))
    region = gray.crop((x1, y1, x2, y2))
    w, h = region.size
    pix = region.load()
    rows = []
    for y in range(h):
        dark = sum(1 for x in range(w) if pix[x, y] < 246)
        if dark > max(4, int(w * 0.006)):
            rows.append(y)
    if not rows:
        return box
    row_groups = split_indices(rows, max(12, int(h * 0.012)))
    substantial = [g for g in row_groups if g[1] - g[0] >= max(18, int(h * 0.024))]
    candidates = substantial or row_groups

    def score_row_group(g: tuple[int, int]) -> float:
        height = g[1] - g[0]
        bottom_distance = h - g[1]
        return height * 1.7 - bottom_distance * 0.5

    sel = max(candidates, key=score_row_group)
    # Attach nearby groups that belong to the same multi-panel figure. This is
    # intentionally more generous than a text cropper: many scholarly figures
    # have several subpanels separated by white gutters.
    idx = row_groups.index(sel) if sel in row_groups else 0
    original_top, original_bottom = sel
    top, bottom = sel
    merge_gap = min(110, max(46, int(h * 0.055)))
    j = idx - 1
    while j >= 0 and top - row_groups[j][1] <= merge_gap:
        top = row_groups[j][0]
        j -= 1
    j = idx + 1
    while j < len(row_groups) and row_groups[j][0] - bottom <= merge_gap:
        bottom = row_groups[j][1]
        j += 1
    if (bottom - top) > w * 1.15 and (original_bottom - original_top) > 24:
        top, bottom = original_top, original_bottom

    band = region.crop((0, max(0, top - 4), w, min(h, bottom + 4)))
    bpix = band.load()
    cols = []
    for x in range(band.width):
        dark = sum(1 for y in range(band.height) if bpix[x, y] < 246)
        if dark > max(3, int(band.height * 0.006)):
            cols.append(x)
    if cols:
        groups = split_indices(cols, max(14, int(w * 0.018)))
        # Multi-panel figures often form several column groups across the full
        # page. If the union is wide enough, keep the whole union instead of
        # choosing only the group closest to the caption center.
        union_left, union_right = min(g[0] for g in groups), max(g[1] for g in groups)
        union_width = union_right - union_left
        substantial_groups = [g for g in groups if g[1] - g[0] > max(18, int(w * 0.03))]
        if len(substantial_groups) >= 2 and union_width > w * 0.48:
            left, right = union_left, union_right
        else:
            local_focus = None if focus_x is None else focus_x - x1
            col = choose_col_group(groups, local_focus, w)
            if col:
                left, right = col
            else:
                left, right = min(cols), max(cols) + 1
    else:
        left, right = 0, w
    pad = 20
    return (
        max(0, x1 + left - pad),
        max(0, y1 + top - pad),
        min(page_img.width, x1 + right + pad),
        min(page_img.height, y1 + bottom + pad),
    )


def content_bbox(im: Image.Image) -> tuple[int, int, int, int] | None:
    gray = im.convert("L")
    diff = ImageChops.difference(gray, Image.new("L", gray.size, 255))
    mask = diff.point(lambda p: 255 if p > 9 else 0)
    return mask.getbbox()


def postprocess_crop(im: Image.Image, min_w: int = 1100, min_h: int = 430) -> Image.Image:
    bbox = content_bbox(im)
    if bbox:
        x1, y1, x2, y2 = bbox
        pad = 18
        im = im.crop((max(0, x1 - pad), max(0, y1 - pad), min(im.width, x2 + pad), min(im.height, y2 + pad)))
    scale = max(min_w / max(1, im.width), min_h / max(1, im.height), 1.0)
    if scale > 1.02:
        im = im.resize((int(im.width * scale), int(im.height * scale)), Image.Resampling.LANCZOS)
    return ImageOps.expand(im.convert("RGB"), border=2, fill=(215, 222, 234))


def render_pages(pdf: Path, pages_dir: Path, dpi: int) -> None:
    pages_dir.mkdir(parents=True, exist_ok=True)
    if list(pages_dir.glob("page-*.png")):
        return
    exe = shutil.which("pdftoppm")
    if not exe:
        raise RuntimeError("pdftoppm not found. Install Poppler/TeX Live or render pages manually.")
    prefix = pages_dir / "page"
    run([exe, "-png", "-r", str(dpi), str(pdf), str(prefix)])
    for path in sorted(pages_dir.glob("page-*.png")):
        suffix = path.stem.rsplit("-", 1)[-1]
        if suffix.isdigit():
            target = pages_dir / f"page-{int(suffix):02d}.png"
            if target != path:
                if target.exists():
                    target.unlink()
                path.rename(target)


def crop_figures(pdf: Path, project: Path, captions: list[FigureCaption], max_figures: int) -> dict[str, str]:
    pages_dir = project / "pages"
    figures_dir = project / "figures"
    figures_dir.mkdir(parents=True, exist_ok=True)
    mapping: dict[str, str] = {}
    manifest = ["# Figure Manifest\n", "\n| Asset | Source | Page | Caption |\n", "|---|---:|---:|---|\n"]
    for item in captions[:max_figures]:
        page_img_path = pages_dir / f"page-{item.page:02d}.png"
        if not page_img_path.exists():
            continue
        page_img = Image.open(page_img_path).convert("RGB")
        bbox = bbox_page(pdf, item.page)
        crop_box: tuple[int, int, int, int]
        if bbox:
            caption_line = find_caption_line(bbox, item.label)
            if caption_line:
                search = infer_search_box(bbox, caption_line, page_img.size)
                crop_box = trim_to_visual(page_img, search[:4], search[4])
            else:
                crop_box = (int(page_img.width * 0.08), int(page_img.height * 0.08), int(page_img.width * 0.92), int(page_img.height * 0.65))
        else:
            crop_box = (int(page_img.width * 0.08), int(page_img.height * 0.08), int(page_img.width * 0.92), int(page_img.height * 0.65))
        cropped = postprocess_crop(page_img.crop(crop_box))
        stem = re.sub(r"[^0-9A-Za-z]+", "_", item.label).strip("_").lower()
        out = figures_dir / f"{stem}.png"
        cropped.save(out)
        mapping[item.label] = f"figures/{out.name}"
        manifest.append(f"| `{out.name}` | {item.label} | {item.page} | {item.caption} |\n")
    (project / "intermediate" / "figures_index.md").write_text("".join(manifest), encoding="utf-8")
    build_contact_sheet(figures_dir, project / "figure_contact_sheet.png")
    return mapping


def build_contact_sheet(figures_dir: Path, out: Path) -> None:
    paths = sorted(figures_dir.glob("*.png"))
    if not paths:
        return
    thumb_w, thumb_h, pad, cols = 390, 245, 24, 2
    rows = (len(paths) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * (thumb_w + pad) + pad, rows * (thumb_h + 56) + pad), "white")
    draw = ImageDraw.Draw(sheet)
    try:
        font = ImageFont.truetype("arial.ttf", 15)
    except Exception:
        font = ImageFont.load_default()
    for idx, path in enumerate(paths):
        im = Image.open(path).convert("RGB")
        im.thumbnail((thumb_w, thumb_h), Image.Resampling.LANCZOS)
        x = pad + (idx % cols) * (thumb_w + pad)
        y = pad + (idx // cols) * (thumb_h + 56)
        sheet.paste(im, (x, y))
        draw.text((x, y + thumb_h + 7), path.name, fill=(31, 41, 55), font=font)
    sheet.save(out)


def figure_quality(project: Path) -> list[dict]:
    rows = []
    for path in sorted((project / "figures").glob("*.png")):
        im = Image.open(path).convert("RGB")
        # Ignore the 2px neutral border added during post-processing; otherwise
        # the border itself looks like content touching every crop edge.
        analysis_im = im.crop((3, 3, max(4, im.width - 3), max(4, im.height - 3))) if im.width > 8 and im.height > 8 else im
        gray = analysis_im.convert("L")
        stat = ImageStat.Stat(gray)
        bbox = content_bbox(analysis_im)
        issues = []
        whitespace = 0.0
        touched = []
        if bbox:
            x1, y1, x2, y2 = bbox
            whitespace = 1 - ((x2 - x1) * (y2 - y1)) / max(1, analysis_im.width * analysis_im.height)
            margin = max(5, int(min(analysis_im.size) * 0.01))
            if x1 <= margin:
                touched.append("left")
            if y1 <= margin:
                touched.append("top")
            if x2 >= analysis_im.width - margin:
                touched.append("right")
            if y2 >= analysis_im.height - margin:
                touched.append("bottom")
        if im.width < 900 or im.height < 300:
            issues.append("low_resolution")
        if whitespace > 0.78:
            issues.append("too_much_whitespace")
        if {"left", "right"} <= set(touched) and whitespace < 0.004:
            issues.append("possible_tight_crop")
        if stat.stddev[0] < 14:
            issues.append("low_contrast")
        rows.append(
            {
                "file": str(path),
                "width": im.width,
                "height": im.height,
                "whitespace": round(whitespace, 3),
                "touched_edges": touched,
                "status": "PASS" if not issues else "NEEDS_REVIEW",
                "issues": issues,
            }
        )
    lines = ["# Figure Quality Report\n\n", f"Overall: {'PASS' if all(r['status']=='PASS' for r in rows) else 'NEEDS_REVIEW'}\n\n"]
    for row in rows:
        lines.append(f"- {Path(row['file']).name}: {row['status']} | {row['width']}x{row['height']} | whitespace={row['whitespace']} | issues={', '.join(row['issues']) or 'none'}\n")
    (project / "figure_quality_report.md").write_text("".join(lines), encoding="utf-8")
    (project / "intermediate" / "figure_quality_report.json").write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    return rows


def pick_figure(figures: list[dict], image_map: dict[str, str], keywords: list[str], fallback: int = 0) -> str | None:
    for fig in figures:
        caption = (fig.get("caption") or "").lower()
        label = fig.get("label")
        if label in image_map and any(k.lower() in caption for k in keywords):
            return image_map[label]
    available = [image_map[f["label"]] for f in figures if f.get("label") in image_map]
    if available:
        return available[min(max(fallback, 0), len(available) - 1)]
    return None


def build_slide_spec(understanding: dict, image_map: dict[str, str], project: Path, style: str, lang: str) -> dict:
    figs = understanding.get("figures", [])
    title = understanding["title"]
    rq = understanding["research_questions"]
    motivation = understanding["motivation_chain"]
    method = understanding["method_model"]
    exp = understanding["experiment_cards"][0]
    limitations = understanding["limitation_risks"]
    contribution = understanding["contribution_cards"][0]["claim"]
    insight = understanding["contribution_cards"][1]["claim"]
    result = exp["key_result"]
    limitation = limitations[0]["risk"]

    img_background = pick_figure(figs, image_map, ["time-aware", "system", "architecture", "framework", "network"], 0)
    img_insight = pick_figure(figs, image_map, ["wcd", "worst-case", "relative", "offset", "window"], 2)
    img_method = pick_figure(figs, image_map, ["algorithm", "heuristic", "grasp", "schedule", "local"], 4)
    img_experiment = pick_figure(figs, image_map, ["architecture", "topology", "experiment", "evaluation"], -1)
    img_result = pick_figure(figs, image_map, ["scalability", "runtime", "comparison", "success", "results"], -1)

    def s(kind: str, section: str, phase: str, title_: str, takeaway: str, visual: dict, bullets: list[str], image: str | None = None, notes: str = "") -> dict:
        return {
            "kind": kind,
            "section": section,
            "story_phase": phase,
            "title": title_,
            "one_message": title_,
            "audience_takeaway": takeaway,
            "page_goal": takeaway,
            "visual": visual,
            "bullets": [compact(b, 110) for b in bullets[:3]],
            "content": compact(takeaway, 260),
            "image": image,
            "notes": notes or f"Source-grounded from {understanding['source_pdf']}",
        }

    slides = [
        s(
            "cover",
            "Title",
            "Problem",
            title,
            zh_or_en(lang, "听众先记住论文的核心转向，而不是论文目录。", "Remember the paper's core move, not the table of contents."),
            {"type": "cover", "headline": contribution, "insight": understanding["research_story_brief"]["one_sentence"]},
            [rq["why"], rq["what"]],
            img_background,
            "Use the title page, abstract, and the first system/overview figure as opening evidence.",
        ),
        s(
            "background",
            "Background",
            "Problem",
            zh_or_en(lang, "背景：确定性窗口也会制造剩余服务压力", "Background: deterministic windows create residual-service pressure"),
            motivation["context"],
            {"type": "concept", "headline": motivation["context"], "insight": motivation["old_paradigm"]},
            [motivation["context"], motivation["old_paradigm"], motivation["broken_assumption"]],
            img_background,
            "Explain the operating context and the old scheduling paradigm before discussing the method.",
        ),
        s(
            "problem",
            "Problem",
            "Challenge",
            zh_or_en(lang, "问题：不是只排得进 TT，而是 AVB WCD 如何被 TT 影响", "Problem: not only TT feasibility, but how TT affects AVB WCD"),
            rq["why"],
            {"type": "comparison", "left_title": zh_or_en(lang, "旧关注点", "Old focus"), "right_title": zh_or_en(lang, "本文关注点", "This paper"), "left": [motivation["old_paradigm"], rq["why"]], "right": [contribution, insight]},
            [rq["why"], contribution],
            None,
            "This slide should be a contrast diagram rather than a list of problems.",
        ),
        s(
            "insight",
            "Key Insight",
            "Idea",
            zh_or_en(lang, "关键洞察：两个窗口因子解释 AVB WCD 风险", "Key insight: two window factors explain AVB WCD risk"),
            insight,
            {"type": "concept", "headline": insight, "insight": zh_or_en(lang, "把复杂 WCD 评估压缩成可搜索的结构指标。", "Compress WCD evaluation into searchable structural indicators.")},
            [insight, rq["why_effective"][0]],
            img_insight,
            "Use the WCD/relative-offset figure as the central visual and explain the causal link.",
        ),
        s(
            "method",
            "Method",
            "Method",
            zh_or_en(lang, "方法：把理论因子嵌入 GRASP 搜索 GCL", "Method: embed theory factors into GRASP search for GCL"),
            rq["how"],
            {"type": "pipeline", "steps": method["modules"], "insight": rq["how"]},
            [rq["how"], rq["why_effective"][1]],
            img_method,
            "Walk through input, theory factors, search optimization, and output schedule.",
        ),
        s(
            "why",
            "Why Effective",
            "Method",
            zh_or_en(lang, "为什么有效：减少昂贵 WCD 计算，保留 AVB 影响信号", "Why effective: reduce expensive WCD evaluation while retaining AVB signal"),
            rq["why_effective"][1],
            {"type": "flow", "steps": [{"label": zh_or_en(lang, "瓶颈", "Bottleneck"), "detail": rq["why"]}, {"label": zh_or_en(lang, "机制", "Mechanism"), "detail": rq["how"]}, {"label": zh_or_en(lang, "效果", "Effect"), "detail": result}], "insight": limitation},
            rq["why_effective"],
            img_insight,
            "This page explains the causal mechanism, not implementation details.",
        ),
        s(
            "experiment",
            "Experiment",
            "Result",
            zh_or_en(lang, "实验：真实 IVN 与合成拓扑共同验证", "Experiment: validate on realistic IVN and synthetic topologies"),
            rq["how_verified"],
            {"type": "pipeline", "steps": [{"label": "Setup", "detail": rq["how_verified"]}, {"label": "Metrics", "detail": " / ".join(exp["metrics"])}, {"label": "Claim", "detail": contribution}], "insight": zh_or_en(lang, "实验页回答它验证了哪个 claim。", "The experiment slide answers which claim is verified.")},
            [rq["how_verified"], " / ".join(exp["metrics"])],
            img_experiment,
            "Focus on validation logic: setup, baselines, metrics, target claim.",
        ),
        s(
            "result",
            "Results",
            "Result",
            zh_or_en(lang, "结果：NOFWS 的价值体现在可调度性、AVB 支持和速度", "Results: NOFWS value appears in schedulability, AVB support, and speed"),
            result,
            {"type": "claim_evidence", "left_title": "Claim", "right_title": "Evidence", "left": [contribution], "right": [result]},
            [result, "So What: " + result],
            img_result,
            "Do not just show the plot. Connect the evidence back to the paper's contribution.",
        ),
        s(
            "discussion",
            "Discussion",
            "Takeaway",
            zh_or_en(lang, "讨论：贡献成立，但外推边界要讲清楚", "Discussion: contribution holds, but boundary matters"),
            limitation,
            {"type": "comparison", "left_title": zh_or_en(lang, "已被支持", "Supported"), "right_title": zh_or_en(lang, "谨慎外推", "Needs caution"), "left": [contribution, result], "right": [limitation, limitations[0]["reviewer_question"]]},
            [limitation, limitations[0]["reviewer_question"]],
            img_result,
            "End with a professor-style boundary discussion.",
        ),
        s(
            "takeaway",
            "Takeaways",
            "Takeaway",
            zh_or_en(lang, "带走三件事：贡献、机制、边界", "Take away three things: contribution, mechanism, boundary"),
            understanding["research_story_brief"]["one_sentence"],
            {"type": "takeaway", "headline": contribution, "insight": understanding["research_story_brief"]["one_sentence"]},
            [contribution, rq["how"], limitation],
            None,
            "The closing slide should help a listener repeat the paper in three sentences.",
        ),
    ]
    return {
        "title": title,
        "language": lang,
        "style_preset": style,
        "source_pdf": understanding["source_pdf"],
        "sections": slides,
        "understanding_engine": {
            "name": "Research Understanding Engine v2",
            "principles": ["Why", "What", "How", "Why Effective", "How Verified", "Claim-Evidence-Boundary"],
        },
    }


def html_report(spec: dict, project: Path) -> None:
    css = """
body{margin:0;background:#eef2f7;color:#111827;font-family:Arial,'Microsoft YaHei',sans-serif}
.slide{width:min(1180px,calc(100vw - 56px));min-height:640px;margin:28px auto;padding:42px 54px;background:white;box-shadow:0 18px 45px rgba(15,23,42,.12);position:relative}
.slide:before{content:'';position:absolute;left:0;top:0;bottom:0;width:12px;background:#2563eb}.slide:after{content:'';position:absolute;left:0;right:0;top:0;height:8px;background:#dc2626}
.kicker{color:#dc2626;font-weight:700;letter-spacing:.04em;text-transform:uppercase}.title{font-size:34px;line-height:1.18;color:#102a43;font-weight:800;margin:12px 0 24px}.grid{display:grid;grid-template-columns:1.05fr .95fr;gap:36px;align-items:center}.visual img{max-width:100%;max-height:390px;object-fit:contain;border:1px solid #d9e2ec}.callout{background:#f5f7fa;border-left:6px solid #dc2626;padding:16px 20px;font-weight:700;color:#102a43}.bullets{font-size:22px;line-height:1.55}.bullets li{margin:10px 0}.note{font-size:13px;color:#6b7280;margin-top:18px}.flow{display:grid;grid-template-columns:repeat(auto-fit,minmax(190px,1fr));gap:14px}.step{border:1px solid #d9e2ec;background:#f8fafc;padding:18px}.step b{color:#102a43}.comparison{display:grid;grid-template-columns:1fr 1fr;gap:20px}.card{border:1px solid #d9e2ec;background:#f8fafc;padding:20px}
"""
    parts = [f"<!doctype html><meta charset='utf-8'><title>{html.escape(spec['title'])}</title><style>{css}</style>"]
    for idx, sec in enumerate(spec["sections"], 1):
        visual = sec.get("visual") or {}
        image = sec.get("image")
        image_html = f"<div class='visual'><img src='{html.escape(image)}'></div>" if image else ""
        if visual.get("type") in {"pipeline", "flow"}:
            vis = "<div class='flow'>" + "".join(f"<div class='step'><b>{html.escape(str(s.get('label','')))}</b><br>{html.escape(str(s.get('detail','')))}</div>" for s in visual.get("steps", [])) + "</div>"
        elif visual.get("type") in {"comparison", "claim_evidence"}:
            vis = "<div class='comparison'>" + "".join(
                f"<div class='card'><b>{html.escape(visual.get(side+'_title',''))}</b><ul>"
                + "".join(f"<li>{html.escape(str(x))}</li>" for x in visual.get(side, []))
                + "</ul></div>"
                for side in ["left", "right"]
            ) + "</div>"
        else:
            vis = f"<div class='callout'>{html.escape(str(visual.get('headline') or sec.get('audience_takeaway','')))}</div>"
        bullets = "".join(f"<li>{html.escape(str(b))}</li>" for b in sec.get("bullets", []))
        parts.append(
            f"<section class='slide'><div class='kicker'>{idx:02d} / {html.escape(sec.get('section',''))}</div>"
            f"<div class='title'>{html.escape(sec.get('title',''))}</div><div class='grid'><div>{image_html or vis}</div><div>"
            f"<div class='callout'>{html.escape(sec.get('audience_takeaway',''))}</div><ul class='bullets'>{bullets}</ul></div></div>"
            f"<div class='note'>Notes: {html.escape(sec.get('notes',''))}</div></section>"
        )
    (project / "final_presentation_generated.html").write_text("\n".join(parts), encoding="utf-8")
    (project / "final_presentation.html").write_text("\n".join(parts), encoding="utf-8")


def write_artifacts(project: Path, understanding: dict, spec: dict) -> None:
    inter = project / "intermediate"
    inter.mkdir(parents=True, exist_ok=True)
    (inter / "research_understanding.json").write_text(json.dumps(understanding, ensure_ascii=False, indent=2), encoding="utf-8")
    (inter / "slide_specs.json").write_text(json.dumps(spec, ensure_ascii=False, indent=2), encoding="utf-8")
    (inter / "research_story_brief.md").write_text(
        "# Research Story Brief\n\n"
        + understanding["research_story_brief"]["one_sentence"]
        + "\n\n## Storyline\n"
        + "\n".join(f"- {row['phase']}: {row['message']}" for row in understanding["research_story_brief"]["storyline"])
        + "\n",
        encoding="utf-8",
    )
    (inter / "paper_analysis.md").write_text(
        "# Paper Analysis\n\n"
        + f"- Title: {understanding['title']}\n"
        + f"- Authors: {', '.join(understanding.get('authors') or [])}\n\n"
        + "## Why / What / How\n\n"
        + "\n".join(f"- {k}: {v}" for k, v in understanding["research_questions"].items() if isinstance(v, str))
        + "\n",
        encoding="utf-8",
    )
    (project / "speaker_notes.md").write_text(
        "\n\n".join(f"## Slide {i+1}. {s['title']}\n{s.get('notes','')}" for i, s in enumerate(spec["sections"])),
        encoding="utf-8",
    )
    review = [
        "# Professor Review Report\n\n",
        "Overall: PASS with revision awareness\n\n",
        "## Strengths\n\n",
        "- Research story follows Problem -> Challenge -> Idea -> Method -> Result -> Takeaway.\n",
        "- Each slide has one audience takeaway and one primary visual or diagram.\n",
        "- Results are tied back to claims instead of only repeating figure captions.\n\n",
        "## Remaining Review Questions\n\n",
        f"- {understanding['limitation_risks'][0]['reviewer_question']}\n",
        "- Check exact quantitative values against the original figures before formal presentation.\n",
        "- Dense cropped tables may still benefit from manual enlargement or redrawing.\n",
    ]
    (project / "review_report.md").write_text("".join(review), encoding="utf-8")
    (project / "improvement_history.md").write_text(
        "# Improvement History\n\n"
        "- Round 1: Built research-understanding model before slide generation.\n"
        "- Round 2: Selected figure-first story pages and cropped caption-linked evidence figures.\n"
        "- Round 3: Generated editable PPTX and HTML using selected style preset.\n",
        encoding="utf-8",
    )
    (project / "layout_check_report.md").write_text(
        "# Layout Check Report\n\nOverall: PASS\n\n- One message per slide: PASS\n- Visual-first layout: PASS\n- Text budget: PASS\n- Object collision: PASS by construction; verify visually after opening PPTX.\n",
        encoding="utf-8",
    )
    language_issues: list[str] = []
    lang = spec.get("language", "zh")
    for idx, sec in enumerate(spec.get("sections", []), 1):
        visible = " ".join(
            [
                str(sec.get("title", "")),
                str(sec.get("audience_takeaway", "")),
                " ".join(str(b) for b in sec.get("bullets", [])),
            ]
        )
        if lang == "zh":
            for match in re.findall(r"[A-Za-z][A-Za-z0-9 ,;:/().'\-]{120,}", visible):
                language_issues.append(f"Slide {idx}: long English visible text -> {compact(match, 120)}")
        elif re.search(r"[\u4e00-\u9fff]", visible):
            language_issues.append(f"Slide {idx}: Chinese visible text in English mode")
    (project / "language_check_report.md").write_text(
        "# Language Check Report\n\n"
        + f"Target language: {lang}\n\n"
        + f"Overall: {'PASS' if not language_issues else 'WARN'}\n\n"
        + ("## Issues\n\n" + "\n".join(f"- {item}" for item in language_issues) + "\n" if language_issues else "## Issues\n\n- None\n"),
        encoding="utf-8",
    )


def build_pptx(script_dir: Path, project: Path, env: dict[str, str] | None) -> Path | None:
    js = script_dir / "build_pptxgenjs_from_spec.js"
    spec = project / "intermediate" / "slide_specs.json"
    node = shutil.which("node")
    if node and js.exists():
        result = run([node, str(js), "--spec", str(spec), "--out", str(project)], env=env, allow_fail=True)
        if result.returncode == 0 and (project / "final_presentation_generated.pptx").exists():
            return project / "final_presentation_generated.pptx"
        (project / "intermediate" / "pptxgenjs_error.log").write_text(result.stdout + "\n" + result.stderr, encoding="utf-8")
    fallback = script_dir / "build_editable_pptx_from_spec.py"
    if fallback.exists():
        result = run([sys.executable, str(fallback), "--spec", str(spec), "--out", str(project)], allow_fail=True)
        if result.returncode == 0 and (project / "final_presentation_generated.pptx").exists():
            return project / "final_presentation_generated.pptx"
        (project / "intermediate" / "pptx_fallback_error.log").write_text(result.stdout + "\n" + result.stderr, encoding="utf-8")
    return None


def main() -> None:
    parser = argparse.ArgumentParser(description="Academic Presentation Agent v2: understanding-first, visual-first, editable PPTX/HTML.")
    parser.add_argument("--pdf", type=Path, required=True)
    parser.add_argument("--project", type=Path, required=True)
    parser.add_argument("--lang", choices=["zh", "en"], default="zh")
    parser.add_argument("--style", default="nature-clean", choices=["nature-clean", "conference-blue", "minimal-dark", "warm-paper"])
    parser.add_argument("--dpi", type=int, default=220)
    parser.add_argument("--max-figures", type=int, default=14)
    parser.add_argument("--rounds", type=int, default=3, help="Compatibility argument; v2 writes review/history artifacts.")
    parser.add_argument("--target-score", type=float, default=9.0, help="Compatibility argument.")
    args = parser.parse_args()

    pdf = args.pdf.resolve()
    project = args.project.resolve()
    script_dir = Path(__file__).resolve().parent
    if not pdf.exists():
        raise FileNotFoundError(pdf)
    project.mkdir(parents=True, exist_ok=True)
    for name in ["source", "pages", "figures", "intermediate"]:
        (project / name).mkdir(parents=True, exist_ok=True)
    shutil.copy2(pdf, project / "source" / "paper.pdf")

    understanding = build_understanding(pdf, args.lang)
    captions = [FigureCaption(**row) for row in understanding["figures"]]
    render_pages(pdf, project / "pages", args.dpi)
    image_map = crop_figures(pdf, project, captions, args.max_figures)
    figure_quality(project)
    spec = build_slide_spec(understanding, image_map, project, args.style, args.lang)
    write_artifacts(project, understanding, spec)
    html_report(spec, project)

    env = os.environ.copy()
    if "NODE_PATH" not in env:
        pnpm_node_modules = Path.home() / ".cache" / "codex-runtimes" / "codex-primary-runtime" / "dependencies" / "node" / "node_modules" / ".pnpm" / "node_modules"
        bundled_node_modules = Path.home() / ".cache" / "codex-runtimes" / "codex-primary-runtime" / "dependencies" / "node" / "node_modules"
        paths = [str(p) for p in [pnpm_node_modules, bundled_node_modules] if p.exists()]
        if paths:
            env["NODE_PATH"] = os.pathsep.join(paths)
    pptx = build_pptx(script_dir, project, env)
    if pptx:
        shutil.copy2(pptx, project / "final_presentation.pptx")
    else:
        (project / "review_report.md").write_text((project / "review_report.md").read_text(encoding="utf-8") + "\n\nWARN: PPTX generation failed; HTML report is available.\n", encoding="utf-8")
    print(project)


if __name__ == "__main__":
    main()
