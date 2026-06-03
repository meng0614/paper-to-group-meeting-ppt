#!/usr/bin/env python
from __future__ import annotations

import argparse
import json
from pathlib import Path


def zh_template() -> dict:
    return {
        "title": "Visual-first Academic Presentation",
        "subtitle": "Paper group meeting talk",
        "language": "zh",
        "style": {
            "primary_color": "0E2557",
            "secondary_color": "4B649F",
            "accent_color": "FF0000",
            "neutral_color": "6B7280",
            "light_color": "F4F7FB",
            "title_font": "Microsoft YaHei",
            "body_font": "Microsoft YaHei",
            "title_size": 30,
            "body_size": 19,
            "layout": "visual-first",
            "animation": "disable",
        },
        "slides": [
            {
                "kind": "cover",
                "title": "论文标题：用一句话说明工作价值",
                "subtitle": "作者 / 会议 / 汇报人",
                "page_goal": "观众知道这篇论文研究什么，以及为什么值得听。",
                "visual": {"type": "concept", "headline": "One paper, one central question"},
                "content": "只放论文标题、作者信息和一句高层次定位。",
                "bullets": ["研究对象", "核心问题", "主要结论"],
                "notes": "Source: paper title page. 开场不要读摘要，先用一句话说清楚这篇论文解决的真实问题。",
            },
            {
                "kind": "background",
                "title": "为什么这个问题重要：应用场景正在制造新的系统压力",
                "page_goal": "观众 5 秒内看到应用场景与技术压力之间的关系。",
                "visual": {
                    "type": "pipeline",
                    "steps": [
                        {"label": "Real-world need", "detail": "业务或应用场景"},
                        {"label": "System pressure", "detail": "规模、实时性、可靠性"},
                        {"label": "Research gap", "detail": "现有机制无法直接满足"},
                    ],
                    "insight": "背景页必须用场景图或系统图解释需求来源，而不是堆文字。",
                },
                "content": "用 2-3 个短标签解释场景、压力和研究缺口。",
                "bullets": ["场景带来新约束", "现有系统假设被打破"],
                "notes": "Source: paper introduction and motivation. 讲解时从真实场景开始，再过渡到论文要解决的问题。",
            },
            {
                "kind": "problem",
                "title": "现有方法的问题不是单点缺陷，而是与本文场景不匹配",
                "page_goal": "观众看到 Existing vs Target 的冲突。",
                "visual": {
                    "type": "comparison",
                    "left_title": "Existing setting",
                    "right_title": "Paper setting",
                    "left": ["较小规模", "单一假设", "静态或简化约束"],
                    "right": ["更大规模", "异构环境", "端到端约束"],
                    "insight": "研究问题来自场景变化导致的假设失效。",
                },
                "content": "不要罗列 5 个问题，只解释最关键的不匹配。",
                "bullets": ["核心矛盾", "为什么旧方法不够"],
                "notes": "Source: related work and problem formulation. 这一页要让听众明白：作者不是为了改算法而改算法。",
            },
            {
                "kind": "method",
                "title": "核心思想：把复杂问题改写成可以被系统处理的流程",
                "page_goal": "观众 30 秒内理解方法全貌。",
                "visual": {
                    "type": "pipeline",
                    "steps": [
                        {"label": "Input", "detail": "论文问题输入"},
                        {"label": "Representation", "detail": "建模或抽象"},
                        {"label": "Decision", "detail": "算法/机制"},
                        {"label": "Output", "detail": "性能或保证"},
                    ],
                    "insight": "方法页应展示数据流、控制流或决策流。",
                },
                "content": "用少量文字解释每个模块的角色。",
                "bullets": ["输入是什么", "关键转换是什么", "输出保证是什么"],
                "notes": "Source: method overview. 不讲细节公式，先建立听众对方法整体结构的理解。",
            },
            {
                "kind": "algorithm",
                "title": "算法页应讲决策逻辑，而不是让听众读伪代码",
                "page_goal": "观众理解算法每一步为什么存在。",
                "visual": {
                    "type": "flow",
                    "steps": [
                        {"label": "State", "detail": "当前系统状态"},
                        {"label": "Decision", "detail": "选择动作或策略"},
                        {"label": "Constraint check", "detail": "检查可行性"},
                        {"label": "Update", "detail": "更新结果"},
                    ],
                    "insight": "把伪代码重画为状态-决策-约束-更新流程。",
                },
                "content": "只保留输入、输出、关键决策和复杂度/直觉。",
                "bullets": ["输入/输出", "核心决策", "可行性检查"],
                "notes": "Source: algorithm section. 伪代码可放 notes，slide 上优先展示决策流程。",
            },
            {
                "kind": "experiment",
                "title": "实验设计必须回答：作者如何证明方法真的有效",
                "page_goal": "观众看到 setup、baseline、metric 三者如何支撑结论。",
                "visual": {
                    "type": "pipeline",
                    "steps": [
                        {"label": "Setup", "detail": "数据/拓扑/任务"},
                        {"label": "Baselines", "detail": "对比方法"},
                        {"label": "Metrics", "detail": "关键指标"},
                        {"label": "Claim", "detail": "要证明什么"},
                    ],
                    "insight": "实验页不是参数表，而是验证逻辑图。",
                },
                "content": "只保留影响结论可信度的设置。",
                "bullets": ["实验对象", "对比基线", "评价指标"],
                "notes": "Source: experiment section. 讲清楚为什么这些实验能支撑论文 claim。",
            },
            {
                "kind": "result",
                "title": "结果页必须把趋势转化成 So What",
                "page_goal": "观众看到关键提升和它意味着什么。",
                "visual": {
                    "type": "result_bar",
                    "items": [
                        {"label": "Baseline", "value": 70},
                        {"label": "Proposed", "value": 88, "highlight": True}
                    ],
                    "unit": "%",
                    "so_what": "So What: 关键指标显著提升，说明方法在目标场景有效。",
                },
                "content": "重绘图表，删除无关曲线，标出最佳结果和关键提升。",
                "bullets": ["保留核心趋势", "标注最佳结果", "解释实际意义"],
                "notes": "Source: results section. 不直接贴复杂原图，优先重画趋势并解释 So What。",
            },
            {
                "kind": "closing",
                "title": "Takeaways：用贡献、创新和局限结束，而不是重复摘要",
                "page_goal": "观众离开时记住这篇论文最重要的一句话。",
                "visual": {"type": "concept", "headline": "Contribution / Novelty / Limitation"},
                "content": "明确最大贡献、最大创新和最大局限。",
                "bullets": ["最大贡献：", "最大创新：", "最大局限："],
                "notes": "Source: conclusion and discussion. 结尾要帮助组会讨论，而不是复述前面内容。",
            },
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Create a visual-first slide spec template.")
    parser.add_argument("--project", type=Path, required=True)
    parser.add_argument("--lang", choices=["zh"], default="zh")
    args = parser.parse_args()
    spec = zh_template()
    out = args.project / "intermediate" / "slide_specs.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(spec, ensure_ascii=False, indent=2), encoding="utf-8")
    print(out)


if __name__ == "__main__":
    main()
