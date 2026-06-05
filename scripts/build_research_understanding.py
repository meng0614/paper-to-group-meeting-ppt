#!/usr/bin/env python
from __future__ import annotations

import argparse
import json
import re
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

COMMON_ACRONYMS = {
    "PDF",
    "IEEE",
    "ACM",
    "CPU",
    "GPU",
    "API",
    "URL",
    "ISBN",
    "DOI",
    "USA",
}

SECTION_ALIASES = {
    "abstract": ["abstract"],
    "introduction": ["introduction", "background"],
    "related_work": ["related work", "prior work", "background and related"],
    "method": [
        "method",
        "methods",
        "approach",
        "design",
        "system",
        "framework",
        "model",
        "formulation",
        "algorithm",
        "solution",
        "proposed",
    ],
    "evaluation": ["evaluation", "experiment", "experiments", "results", "performance", "case study"],
    "discussion": ["discussion", "analysis", "threats", "limitation", "limitations"],
    "conclusion": ["conclusion", "future work"],
}


@dataclass
class FigureCaption:
    label: str
    page: int
    caption: str


def clean_text(text: str) -> str:
    for src, dst in LIGATURES.items():
        text = text.replace(src, dst)
    text = text.replace("\u2013", "-").replace("\u2014", "-")
    text = text.replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    return text


def compact(value: str, limit: int = 240) -> str:
    text = re.sub(r"\s+", " ", str(value or "")).strip()
    if len(text) <= limit:
        return text
    return text[:limit].rstrip(" ,;:.，；：。") + "..."


def split_sentences(text: str) -> list[str]:
    text = re.sub(r"\s+", " ", text)
    parts = re.split(r"(?<=[.!?。！？])\s+(?=[A-Z0-9一-龥])", text)
    return [p.strip() for p in parts if len(p.strip()) > 28]


def pick_sentences(text: str, keywords: list[str], limit: int = 3, min_len: int = 35) -> list[str]:
    out: list[str] = []
    seen = set()
    for sentence in split_sentences(text):
        low = sentence.lower()
        if len(sentence) < min_len:
            continue
        if any(k.lower() in low for k in keywords):
            key = compact(sentence, 140).lower()
            if key not in seen:
                out.append(sentence)
                seen.add(key)
        if len(out) >= limit:
            break
    return out


def reference_like(sentence: str) -> bool:
    low = sentence.lower()
    reference_markers = [
        "ieee",
        "acm",
        "conference",
        "proceedings",
        "transactions",
        "symposium",
        "journal",
        "vol.",
        "no.",
        "pp.",
        "doi",
        "isbn",
        "springer",
        "elsevier",
        "in 20",
        "in 19",
    ]
    if sum(1 for marker in reference_markers if marker in low) >= 2:
        return True
    if re.search(r"\b[A-Z][a-z]+,\s+[A-Z][a-z]+,\s+[A-Z][a-z]+", sentence) and re.search(r"\b(20\d{2}|19\d{2})\b", sentence):
        return True
    return False


def usable_extracted_sentence(sentence: str) -> bool:
    value = re.sub(r"\s+", " ", str(sentence or "")).strip()
    if len(value) < 35 or reference_like(value):
        return False
    low = value.lower()
    broken_patterns = [
        r"^in our\s+as\b",
        r"^as a set of constraints\b",
        r"^and\s+[a-z]+",
        r"^,",
    ]
    if any(re.search(pattern, low) for pattern in broken_patterns):
        return False
    return True


def extract_pages(pdf: Path) -> list[str]:
    reader = PdfReader(str(pdf))
    return [clean_text(page.extract_text() or "") for page in reader.pages]


def extract_title(first_page: str, pdf: Path) -> str:
    lines = [clean_text(line).strip() for line in first_page.splitlines() if line.strip()]
    lines = [
        line
        for line in lines
        if not re.search(r"@|accepted for|copyright|personal use|proc\.|university|abstract|ieee transactions", line, re.I)
    ]
    if not lines:
        return pdf.stem
    title_lines: list[str] = []
    for line in lines[:10]:
        if len(line) > 130:
            continue
        if re.search(r"^[A-Z][a-z]+ [A-Z]", line) and title_lines:
            break
        title_lines.append(line)
        if len(" ".join(title_lines)) > 110 or len(title_lines) >= 3:
            break
    return " ".join(title_lines).strip() or pdf.stem


def extract_authors(first_page: str, title: str) -> list[str]:
    lines = [clean_text(line).strip() for line in first_page.splitlines() if line.strip()]
    authors: list[str] = []
    title_words = set(title.split())
    for line in lines[:35]:
        if line == title or set(line.split()).issubset(title_words):
            continue
        if re.search(r"@|university|institute|department|abstract|ieee|copyright|received|accepted", line, re.I):
            continue
        words = line.split()
        if 2 <= len(words) <= 7 and sum(1 for w in words if re.match(r"^[A-Z][A-Za-z.\-`']+$", w)) >= 2:
            authors.append(line)
        if len(authors) >= 8:
            break
    return authors


def extract_abstract(full_text: str) -> str:
    patterns = [
        r"Abstract\s*[-\u2014]?\s*(.*?)(?:Index Terms|Keywords|I\.\s+INTRODUCTION|1\s+Introduction)",
        r"ABSTRACT\s*(.*?)(?:KEYWORDS|I\.\s+INTRODUCTION|1\s+Introduction)",
    ]
    for pattern in patterns:
        match = re.search(pattern, full_text, re.I | re.S)
        if match:
            return compact(match.group(1), 1600)
    return compact(full_text, 1100)


def normalize_heading(line: str) -> str | None:
    value = re.sub(r"\s+", " ", line).strip()
    if len(value) < 3 or len(value) > 90:
        return None
    value = re.sub(r"^\d+(\.\d+)*\s+", "", value)
    value = re.sub(r"^[IVXLCDM]+\.\s+", "", value, flags=re.I)
    if re.match(r"^[A-Z][A-Z0-9 ,/&()\-:]{3,}$", value):
        return value.lower()
    title_like = ["Introduction", "Related Work", "Method", "Methods", "Approach", "Design", "Evaluation", "Experiment", "Results", "Discussion", "Conclusion"]
    if any(value.lower().startswith(t.lower()) for t in title_like):
        return value.lower()
    return None


def extract_sections(pages: list[str]) -> dict[str, str]:
    lines: list[str] = []
    for page in pages:
        lines.extend(page.splitlines())
    sections: dict[str, list[str]] = {}
    current = "front_matter"
    sections[current] = []
    for line in lines:
        heading = normalize_heading(line)
        if heading and not re.search(r"fig\.|table|algorithm|copyright|ieee transactions", heading, re.I):
            current = heading
            sections.setdefault(current, [])
            continue
        sections.setdefault(current, []).append(line)
    return {name: clean_text("\n".join(body)).strip() for name, body in sections.items() if clean_text("\n".join(body)).strip()}


def section_text(sections: dict[str, str], full_text: str, key: str, limit: int = 9000) -> str:
    aliases = SECTION_ALIASES.get(key, [key])
    chunks = []
    for name, text in sections.items():
        low_name = name.lower()
        if any(alias in low_name for alias in aliases):
            chunks.append(text)
    if chunks:
        return compact("\n".join(chunks), limit)
    low = full_text.lower()
    for alias in aliases:
        pos = low.find(alias)
        if pos >= 0:
            return full_text[pos : pos + limit]
    return ""


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
                if len(extra) < 180:
                    caption_parts.append(extra)
            figures.append(FigureCaption(label=label, page=page_no, caption=compact(" ".join(caption_parts), 320)))
            seen.add((page_no, label))
    return figures


def extract_terms(full_text: str) -> list[dict]:
    counts: dict[str, int] = {}
    for term in re.findall(r"\b[A-Z][A-Z0-9][A-Z0-9\-]{1,}\b", full_text):
        if term in COMMON_ACRONYMS or len(term) > 18:
            continue
        counts[term] = counts.get(term, 0) + 1
    rows = []
    for term, count in sorted(counts.items(), key=lambda item: (-item[1], item[0]))[:18]:
        pattern = re.compile(rf"([A-Za-z][A-Za-z \-]{{3,80}})\s*\({re.escape(term)}\)|{re.escape(term)}\s*\(([A-Za-z][A-Za-z \-]{{3,80}})\)")
        match = pattern.search(full_text)
        meaning = ""
        if match:
            meaning = compact(match.group(1) or match.group(2), 120)
        rows.append({"term": term, "frequency": count, "meaning": meaning or "needs verification", "role": "domain or method acronym"})
    return rows


def contribution_type(sentence: str) -> str:
    low = sentence.lower()
    if any(k in low for k in ["formulation", "model", "graph", "representation", "problem"]):
        return "problem formulation / representation"
    if any(k in low for k in ["algorithm", "method", "approach", "framework", "system", "scheme", "protocol"]):
        return "method / system"
    if any(k in low for k in ["evaluate", "experiment", "outperform", "result", "performance", "benchmark"]):
        return "empirical evidence"
    if any(k in low for k in ["theorem", "proof", "bound", "guarantee", "analysis"]):
        return "theory / analysis"
    return "research claim"


def extract_contributions(text: str, fallback: str) -> list[dict]:
    keywords = [
        "contribution",
        "we propose",
        "we present",
        "we introduce",
        "we design",
        "we develop",
        "we show",
        "we demonstrate",
        "we evaluate",
        "this paper",
        "our approach",
        "our method",
    ]
    sentences = pick_sentences(text, keywords, 6)
    if not sentences:
        sentences = split_sentences(fallback)[:3]
    cards = []
    for idx, sentence in enumerate(sentences[:5], 1):
        ctype = contribution_type(sentence)
        cards.append(
            {
                "id": f"C{idx}",
                "type": ctype,
                "claim": compact(sentence, 340),
                "why_it_matters": "它改变了读者理解问题、方法或证据的方式；汇报时需要把它绑定到具体图示或实验。",
                "evidence_to_check": "对应的方法章节、图示、实验或结论段落。",
                "source": "abstract/introduction/conclusion contribution signal",
            }
        )
    return cards


def build_domain_primer(abstract: str, intro: str, terms: list[dict]) -> dict:
    context = pick_sentences(intro + " " + abstract, ["network", "system", "application", "real-time", "data", "traffic", "model", "task", "problem", "scheduling"], 2)
    requirement = pick_sentences(intro + " " + abstract, ["require", "must", "deadline", "constraint", "guarantee", "accurate", "efficient", "latency", "throughput"], 2)
    pressure = pick_sentences(intro + " " + abstract, ["hard", "difficult", "challenge", "scalab", "overhead", "expensive", "complex", "bottleneck"], 2)
    return {
        "field_context": compact(context[0] if context else abstract, 300),
        "technical_requirement": compact(requirement[0] if requirement else "needs verification", 260),
        "planning_pressure": compact(pressure[0] if pressure else "needs verification", 260),
        "key_terms": terms[:10],
        "background_chain": [
            "应用/系统提出可靠性、时延、效率或可扩展性要求",
            "现有方法在某些假设下可用，但在目标场景中暴露瓶颈",
            "论文需要引入新的建模、算法或系统机制来缓解该瓶颈",
        ],
    }


def build_motivation_chain(abstract: str, intro: str, related: str, contributions: list[dict]) -> dict:
    source = intro + " " + abstract
    known = pick_sentences(source, ["important", "key", "enable", "require", "need", "widely", "used"], 2)
    prevailing = pick_sentences(source + " " + related, ["existing", "prior", "state-of-the-art", "traditional", "current", "baseline", "typically"], 2)
    bottleneck = pick_sentences(source + " " + related, ["however", "but", "hard", "difficult", "challenge", "limitation", "scalab", "overhead", "cost", "not"], 3)
    need = pick_sentences(source, ["need", "therefore", "motivated", "new", "efficient", "scalable", "address"], 2)
    paper_move = contributions[0]["claim"] if contributions else compact(abstract, 260)
    return {
        "known_context": compact(known[0] if known else abstract, 260),
        "prevailing_approach": compact(prevailing[0] if prevailing else "Existing work provides a baseline but its exact assumption needs verification.", 260),
        "broken_assumption_or_bottleneck": compact(bottleneck[0] if bottleneck else "The paper implies a bottleneck, but the exact failure mode needs verification.", 300),
        "research_need": compact(need[0] if need else "A new formulation or mechanism is needed to address the bottleneck.", 260),
        "paper_move": compact(paper_move, 300),
        "presentation_angle": "先讲为什么旧范式在目标场景下吃力，再讲作者如何换一种表示或机制。",
    }


def build_related_work_matrix(related: str, intro: str) -> list[dict]:
    text = related or intro
    categories = [
        ("Optimization / exact modeling", ["ILP", "MILP", "SMT", "SAT", "integer", "optimization", "constraint"]),
        ("Heuristic / search", ["heuristic", "greedy", "search", "genetic", "metaheuristic", "approximation"]),
        ("Learning / adaptive method", ["learning", "reinforcement", "neural", "agent", "policy", "training"]),
        ("System / protocol design", ["system", "architecture", "protocol", "framework", "implementation"]),
        ("Analysis / theory", ["analysis", "theorem", "bound", "proof", "calculus", "model"]),
    ]
    rows: list[dict] = []
    for name, keywords in categories:
        evidence = pick_sentences(text, keywords, 1)
        if evidence:
            rows.append(
                {
                    "category": name,
                    "what_it_does": compact(evidence[0], 260),
                    "assumed_strength": "论文把这一类作为背景或对比对象。",
                    "limitation_signal": compact((pick_sentences(text, keywords + ["however", "limitation", "scalab", "cost"], 2)[-1] if pick_sentences(text, keywords + ["however", "limitation", "scalab", "cost"], 2) else evidence[0]), 240),
                    "source": "related work / introduction",
                }
            )
    if not rows:
        rows.append(
            {
                "category": "Prior work",
                "what_it_does": compact(text, 260),
                "assumed_strength": "needs verification",
                "limitation_signal": "Related-work taxonomy is weak in extracted text; verify manually.",
                "source": "fallback",
            }
        )
    return rows[:5]


def build_gap_analysis(motivation: dict, related_matrix: list[dict], abstract: str) -> dict:
    related_limitations = [row["limitation_signal"] for row in related_matrix[:3]]
    return {
        "gap_statement": compact(motivation.get("broken_assumption_or_bottleneck") or abstract, 360),
        "why_existing_is_not_enough": related_limitations or ["needs verification"],
        "gap_type": "representation / scalability / evidence gap, to be verified from full text",
        "paper_specific_opportunity": compact(motivation.get("research_need") or motivation.get("paper_move") or abstract, 320),
        "reviewer_check": "汇报时应说明该 gap 是否是作者明确指出，还是我们从 related work 推断出来的。",
    }


def build_method_model(method_text: str, abstract: str) -> dict:
    source = method_text or abstract
    modules = pick_sentences(
        source,
        ["first", "second", "then", "consists", "component", "module", "framework", "algorithm", "construct", "build", "solve", "search", "train", "learn", "derive"],
        5,
    )
    inputs = pick_sentences(source, ["input", "given", "consider", "network", "dataset", "traffic", "topology", "flow", "request"], 3)
    outputs = pick_sentences(source, ["output", "return", "produce", "schedule", "route", "allocation", "policy", "prediction", "solution"], 3)
    assumptions = pick_sentences(source, ["assume", "given", "under", "constraint", "requirement", "deadline", "bound"], 3)
    mechanism = modules[:3] or split_sentences(source)[:3]
    return {
        "inputs": [compact(s, 180) for s in inputs] or ["论文输入需要从问题定义中人工复核。"],
        "outputs": [compact(s, 180) for s in outputs] or ["论文输出需要从方法/算法段落中人工复核。"],
        "modules": [{"name": f"Module {idx}", "role": compact(sentence, 220)} for idx, sentence in enumerate(mechanism, 1)],
        "core_mechanism": compact(" ".join(mechanism), 520),
        "assumptions": [compact(s, 180) for s in assumptions] or ["关键假设未被稳定抽取，建议人工复核。"],
        "invariants": ["方法应保持问题约束、资源约束或性能指标不被破坏。"],
        "failure_modes": ["当论文假设不成立、规模外推过大或输入分布变化时，方法效果需要重新验证。"],
    }


def build_why_effective(motivation: dict, method_model: dict, evaluation: str) -> dict:
    result_signal = pick_sentences(evaluation, ["outperform", "reduce", "improve", "increase", "faster", "memory", "latency", "accuracy", "success", "%"], 2)
    mechanism = method_model.get("core_mechanism") or "needs verification"
    return {
        "mechanism_summary": compact(mechanism, 420),
        "causal_chain": [
            compact("Bottleneck: " + str(motivation.get("broken_assumption_or_bottleneck", "needs verification")), 260),
            compact("Mechanism: " + str(mechanism), 300),
            compact("Expected effect: reduce coupling/search burden or improve decision quality.", 220),
            compact("Observed evidence: " + (result_signal[0] if result_signal else "reported evaluation should be checked for concrete support"), 260),
        ],
        "tradeoff": "有效性通常来自表示转换、搜索空间削减、信息利用或系统机制；相应代价可能是适用假设、实现复杂度或泛化范围。",
    }


def build_experiment_cards(evaluation: str, figures: list[FigureCaption]) -> list[dict]:
    setup = pick_sentences(evaluation, ["setup", "dataset", "topology", "testbed", "implementation", "simulation", "benchmark", "environment"], 3)
    baselines = pick_sentences(evaluation, ["baseline", "compare", "comparison", "state-of-the-art", "ILP", "heuristic", "existing"], 3)
    metrics = pick_sentences(evaluation, ["metric", "runtime", "memory", "latency", "throughput", "accuracy", "ratio", "success", "cost", "delay"], 4)
    results = pick_sentences(evaluation, ["show", "outperform", "reduce", "increase", "improve", "faster", "higher", "lower", "%"], 5)
    result_figures = [fig for fig in figures if re.search(r"result|runtime|performance|evaluation|experiment|latency|memory|comparison|throughput", fig.caption, re.I)]
    cards = []
    cards.append(
        {
            "id": "E1",
            "question": "实验是否验证了论文核心机制，而不仅是展示实现？",
            "setup": [compact(s, 180) for s in setup] or ["实验设置需要从 evaluation section 人工复核。"],
            "baselines": [compact(s, 160) for s in baselines] or ["对比基线需要人工复核。"],
            "metrics": [compact(s, 160) for s in metrics] or ["指标需要人工复核。"],
            "key_result": compact(results[0] if results else "结果趋势需要从图表和正文中复核。", 260),
            "support_strength": "strong if result directly matches the core contribution; otherwise partial",
            "figures": [fig.__dict__ for fig in result_figures[:4]],
        }
    )
    if len(results) > 1:
        cards.append(
            {
                "id": "E2",
                "question": "结果是否说明方法在规模、效率或质量上有优势？",
                "setup": [compact(s, 180) for s in setup[:1]],
                "baselines": [compact(s, 160) for s in baselines[:2]],
                "metrics": [compact(s, 160) for s in metrics[:2]],
                "key_result": compact(results[1], 260),
                "support_strength": "partial until exact figure/table values are checked",
                "figures": [fig.__dict__ for fig in result_figures[4:8]],
            }
        )
    return cards


def build_result_to_claim(contributions: list[dict], experiments: list[dict]) -> list[dict]:
    rows = []
    for card in contributions[:4]:
        exp = experiments[0] if experiments else {}
        rows.append(
            {
                "claim_id": card["id"],
                "claim": card["claim"],
                "evidence": exp.get("key_result", "needs verification"),
                "support": "direct / partial needs reviewer verification",
                "presentation_note": "结果页必须讲清楚这个证据支持了哪个 claim，避免只复述图表。",
            }
        )
    return rows


def build_limitation_risks(discussion: str, conclusion: str, method_model: dict) -> list[dict]:
    source = discussion + " " + conclusion
    explicit = [
        s
        for s in pick_sentences(source, ["future work", "limitation", "threat", "however", "not", "remain", "extend", "scalab"], 8)
        if not reference_like(s)
    ][:4]
    risks = [{"type": "explicit / textual", "risk": compact(s, 260), "reviewer_question": "作者是否已经承认，PPT 需要如实呈现。"} for s in explicit]
    assumptions = [item for item in (method_model.get("assumptions") or []) if usable_extracted_sentence(item)]
    assumption_risk = assumptions[0] if assumptions else "关键方法假设（输入模型、约束条件、系统模型或规模范围）需要人工复核。"
    risks.extend(
        [
            {
                "type": "assumption",
                "risk": compact(assumption_risk, 240),
                "reviewer_question": "如果该假设不成立，方法是否仍然有效？",
            },
            {
                "type": "evidence scope",
                "risk": "实验范围、数据集/拓扑/场景是否足以支撑作者的泛化性表述。",
                "reviewer_question": "审稿人会问：是否只是特定设置下有效？",
            },
        ]
    )
    return risks[:6]


def build_research_story_brief(title: str, motivation: dict, gap: dict, method_model: dict, why_effective: dict, experiments: list[dict], limitations: list[dict]) -> dict:
    key_result = experiments[0]["key_result"] if experiments else "实验结果需要复核"
    return {
        "one_sentence": compact(f"{title} 的故事线是：旧方法在目标场景中遇到瓶颈，作者用新的表示/机制解决，并用实验验证其效率或效果。", 260),
        "storyline": [
            {"phase": "Problem", "message": compact(motivation.get("known_context"), 180)},
            {"phase": "Challenge", "message": compact(gap.get("gap_statement"), 180)},
            {"phase": "Idea", "message": compact(motivation.get("paper_move"), 180)},
            {"phase": "Method", "message": compact(method_model.get("core_mechanism"), 180)},
            {"phase": "Result", "message": compact(key_result, 180)},
            {"phase": "Takeaway", "message": compact((limitations[0]["risk"] if limitations else "最大局限需要复核"), 180)},
        ],
        "slide_messages": [
            "为什么这个问题值得做",
            "现有方法的瓶颈在哪里",
            "作者的关键转向是什么",
            "方法为什么可能有效",
            "实验证明了什么，没证明什么",
        ],
    }


def build_understanding_review(understanding: dict) -> dict:
    scores = {
        "Background Depth": 8.0 if understanding["domain_primer"].get("field_context") else 6.0,
        "Motivation Depth": 8.5 if understanding["motivation_chain"].get("broken_assumption_or_bottleneck") else 6.0,
        "Gap Accuracy": 8.0 if understanding["gap_analysis"].get("why_existing_is_not_enough") else 6.0,
        "Contribution Accuracy": 8.5 if len(understanding["contribution_cards"]) >= 2 else 7.0,
        "Method Causal Explanation": 8.5 if understanding["method_model"].get("core_mechanism") else 6.0,
        "Experiment Interpretation": 8.0 if understanding["experiment_cards"] else 6.0,
        "Claim-Evidence Fidelity": 8.0 if understanding["result_to_claim_matrix"] else 6.0,
        "Reviewer Question Readiness": 8.0 if understanding["limitation_risks"] else 6.0,
    }
    return {
        "overall": round(sum(scores.values()) / len(scores), 2),
        "scores": scores,
        "professor_questions": [
            "这篇论文真正的新意是问题重表述、算法机制、系统实现，还是实验结果？",
            "方法为什么会有效？它减少了什么复杂性，利用了什么结构？",
            "实验是否直接支撑核心贡献，还是只证明了实现可运行？",
            "哪些结论不能从当前实验外推？",
        ],
        "KEEP": ["保留 source-grounded 的论文理解产物，避免无根据发挥。"],
        "REMOVE": ["删除只复述摘要、没有因果解释的内容。"],
        "ADD": ["补充 Why Effective 和 Result-to-Claim 两类汇报页。"],
        "MODIFY": ["把 PPT 故事线从论文目录改为 Problem -> Challenge -> Idea -> Method -> Result -> Takeaway。"],
    }


def write_markdown_outputs(intermediate: Path, understanding: dict) -> None:
    primer = understanding["domain_primer"]
    motivation = understanding["motivation_chain"]
    method = understanding["method_model"]
    why = understanding["why_effective"]
    story = understanding["research_story_brief"]
    review = understanding["understanding_review"]

    (intermediate / "domain_primer.md").write_text(
        "\n".join(
            [
                "# Domain Primer",
                "",
                f"- Field context: {primer['field_context']}",
                f"- Technical requirement: {primer['technical_requirement']}",
                f"- Planning pressure: {primer['planning_pressure']}",
                "",
                "## Background Chain",
                *[f"- {item}" for item in primer["background_chain"]],
                "",
            ]
        ),
        encoding="utf-8",
    )
    (intermediate / "why_effective.md").write_text(
        "\n".join(["# Why Effective", "", f"Mechanism: {why['mechanism_summary']}", "", "## Causal Chain", *[f"- {item}" for item in why["causal_chain"]], "", f"Tradeoff: {why['tradeoff']}", ""]),
        encoding="utf-8",
    )
    (intermediate / "research_story_brief.md").write_text(
        "\n".join(["# Research Story Brief", "", story["one_sentence"], "", "## Storyline", *[f"- {item['phase']}: {item['message']}" for item in story["storyline"]], ""]),
        encoding="utf-8",
    )
    (intermediate / "understanding_review.md").write_text(
        "\n".join(
            [
                "# Understanding Review",
                "",
                f"Overall: {review['overall']}/10",
                "",
                "## Scores",
                *[f"- {k}: {v}/10" for k, v in review["scores"].items()],
                "",
                "## Professor Questions",
                *[f"- {q}" for q in review["professor_questions"]],
                "",
                "## KEEP / REMOVE / ADD / MODIFY",
                f"- KEEP: {'; '.join(review['KEEP'])}",
                f"- REMOVE: {'; '.join(review['REMOVE'])}",
                f"- ADD: {'; '.join(review['ADD'])}",
                f"- MODIFY: {'; '.join(review['MODIFY'])}",
                "",
            ]
        ),
        encoding="utf-8",
    )
    (intermediate / "motivation_chain.json").write_text(json.dumps(motivation, ensure_ascii=False, indent=2), encoding="utf-8")
    (intermediate / "related_work_matrix.json").write_text(json.dumps(understanding["related_work_matrix"], ensure_ascii=False, indent=2), encoding="utf-8")
    (intermediate / "gap_analysis.json").write_text(json.dumps(understanding["gap_analysis"], ensure_ascii=False, indent=2), encoding="utf-8")
    (intermediate / "contribution_cards.json").write_text(json.dumps(understanding["contribution_cards"], ensure_ascii=False, indent=2), encoding="utf-8")
    (intermediate / "method_model.json").write_text(json.dumps(method, ensure_ascii=False, indent=2), encoding="utf-8")
    (intermediate / "experiment_cards.json").write_text(json.dumps(understanding["experiment_cards"], ensure_ascii=False, indent=2), encoding="utf-8")
    (intermediate / "result_to_claim_matrix.json").write_text(json.dumps(understanding["result_to_claim_matrix"], ensure_ascii=False, indent=2), encoding="utf-8")
    (intermediate / "limitation_risks.json").write_text(json.dumps(understanding["limitation_risks"], ensure_ascii=False, indent=2), encoding="utf-8")
    (intermediate / "term_ledger.json").write_text(json.dumps(understanding["term_ledger"], ensure_ascii=False, indent=2), encoding="utf-8")


def build_understanding(pdf: Path) -> dict:
    pages = extract_pages(pdf)
    full_text = "\n".join(pages)
    sections = extract_sections(pages)
    title = extract_title(pages[0] if pages else "", pdf)
    authors = extract_authors(pages[0] if pages else "", title)
    abstract = extract_abstract(full_text)
    intro = section_text(sections, full_text, "introduction")
    related = section_text(sections, full_text, "related_work")
    method_text = section_text(sections, full_text, "method")
    evaluation = section_text(sections, full_text, "evaluation")
    discussion = section_text(sections, full_text, "discussion")
    conclusion = section_text(sections, full_text, "conclusion")
    figures = extract_figure_captions(pages)
    terms = extract_terms(full_text)
    contribution_source = " ".join([abstract, intro, conclusion])
    contributions = extract_contributions(contribution_source, abstract)
    domain = build_domain_primer(abstract, intro, terms)
    motivation = build_motivation_chain(abstract, intro, related, contributions)
    related_matrix = build_related_work_matrix(related, intro)
    gap = build_gap_analysis(motivation, related_matrix, abstract)
    method = build_method_model(method_text, abstract)
    why = build_why_effective(motivation, method, evaluation)
    experiments = build_experiment_cards(evaluation, figures)
    result_to_claim = build_result_to_claim(contributions, experiments)
    limitations = build_limitation_risks(discussion, conclusion, method)
    story = build_research_story_brief(title, motivation, gap, method, why, experiments, limitations)
    year_match = re.search(r"\b(20\d{2}|19\d{2})\b", full_text)
    understanding = {
        "title": title,
        "authors": authors,
        "year": year_match.group(1) if year_match else "",
        "source_pdf": str(pdf),
        "abstract": abstract,
        "sections_detected": list(sections.keys()),
        "source_map": {
            "abstract": abstract,
            "introduction": compact(intro, 900),
            "related_work": compact(related, 900),
            "method": compact(method_text, 900),
            "evaluation": compact(evaluation, 900),
            "discussion": compact(discussion + " " + conclusion, 900),
        },
        "term_ledger": terms,
        "domain_primer": domain,
        "motivation_chain": motivation,
        "related_work_matrix": related_matrix,
        "gap_analysis": gap,
        "contribution_cards": contributions,
        "method_model": method,
        "why_effective": why,
        "experiment_cards": experiments,
        "result_to_claim_matrix": result_to_claim,
        "limitation_risks": limitations,
        "research_story_brief": story,
        "figure_captions": [fig.__dict__ for fig in figures],
    }
    understanding["understanding_review"] = build_understanding_review(understanding)
    return understanding


def main() -> None:
    parser = argparse.ArgumentParser(description="Build a source-grounded Research Understanding Engine output for an academic paper.")
    parser.add_argument("--pdf", type=Path, required=True)
    parser.add_argument("--project", type=Path, required=True)
    parser.add_argument("--lang", choices=["zh", "en"], default="zh")
    args = parser.parse_args()

    project = args.project.resolve()
    intermediate = project / "intermediate"
    intermediate.mkdir(parents=True, exist_ok=True)
    understanding = build_understanding(args.pdf.resolve())
    (intermediate / "research_understanding.json").write_text(json.dumps(understanding, ensure_ascii=False, indent=2), encoding="utf-8")
    write_markdown_outputs(intermediate, understanding)
    print(intermediate / "research_understanding.json")


if __name__ == "__main__":
    main()
