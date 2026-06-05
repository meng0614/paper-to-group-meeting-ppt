# Research Understanding Landscape

生成日期：2026-06-05

项目：`paper-to-group-meeting-ppt-release`

本文件聚焦“论文理解能力”，不讨论 PPT 排版与视觉设计。当前问题不是能否生成 PPT，而是系统是否真正理解论文：

```text
Why -> What -> How -> Why Effective -> How Verified
```

而不仅仅是：

```text
论文写了什么
```

## 1. 调研方法

本轮按用户要求主动使用 `find skill` 检索以下关键词：

```text
Paper Understanding Agent
Research Agent
Literature Review Agent
Research Insight Extraction
Research Storytelling
Research Motivation Extraction
Contribution Extraction
Method Explanation
Experiment Interpretation
Professor Review
Scientific Reading Assistant
```

原始检索结果保存于：

`C:\Users\30430\Documents\research\outputs\research_understanding_skill_search\raw\`

同时补充分析本地已安装的科研理解、文献综述、审稿和结果解释类 skills：

- `research-lit`
- `comm-lit-review`
- `nature-reader`
- `nature-reviewer`
- `research-review`
- `nature-paper2ppt`
- `paper-claim-audit`
- `result-to-claim`
- `experiment-audit`
- `novelty-check`
- `paper-talk`
- `kill-argument`

## 2. 总体判断

find skill 生态中，“PPT/设计/排版”类 skill 明显多于“深度论文理解”类 skill。真正适合迁移的能力主要分布在四类：

1. Paper Reading / Digest
   - 解决“论文到底在说什么”。
2. Literature Review / Novelty
   - 解决“为什么这个问题值得做，已有工作哪里不够”。
3. Method / Experiment Interpretation
   - 解决“方法为什么可能有效，实验到底证明了什么”。
4. Professor / Reviewer
   - 解决“这个理解是否准确，贡献是否被夸大”。

当前 `paper-to-group-meeting-ppt-release` 最大短板是：它有 presentation pipeline，但没有 research understanding pipeline。现在的 `paper_model` 更像摘要字段集合，而不是研究理解模型。

## 3. Skill Landscape

下面只保留和论文理解相关或可迁移的 skill。明显无关的结果，例如法律 drafting、代码重构、PM 用户画像、开源贡献流程等，仅在附录中标记为不迁移。

### 3.1 Paper Understanding / Scientific Reading

| Skill | Repository | 背景提取 | 动机提取 | 研究空白 | 核心贡献 | 方法有效性 | 实验解读 | 故事线 | 迁移判断 |
|---|---|---|---|---|---|---|---|---|---|
| `chat-with-arxiv` | `qodex-ai/ai-agent-skills` | 从 arXiv 元数据和正文做问答式理解 | 依赖用户追问 | 弱，需要额外 review | 可抽取主要贡献 | 中，适合逐段问答 | 弱到中 | 弱 | 可参考：交互式 paper QA |
| `method-section-explainer` | `a-green-hand-jack/ml-research-skills` | 不负责背景 | 不负责动机 | 弱 | 仅方法相关贡献 | 强，适合拆方法模块、输入输出、机制 | 弱 | 中 | 高价值：迁移到 Method Reasoning Agent |
| `agentic-paper-digest-skill` | `matanle51/agentic-paper-digest-skill` | 可抽摘要/引言信号 | 中 | 中 | 中 | 中 | 中 | 中 | 可作为 paper digest baseline，但不足以支撑深度理解 |
| `analyzing-research-papers` | `seabbs/skills` | 较强，面向研究论文分析 | 较强 | 中到强 | 中到强 | 中 | 中 | 中 | 高价值：适合迁移 paper analysis rubric |
| `deep-read` | `pfangueiro/claude-code-agents` | 强调深读 | 可用于动机追问 | 中 | 中 | 中 | 中 | 中 | 可参考：多轮深读流程 |
| `scientific-skills` | `oimiragieo/agent-studio` | 科研通用能力 | 中 | 中 | 中 | 中 | 中 | 中 | 可参考，但需安装后复核具体实现 |
| `claude-scientific-skills` | `smithery.ai` | 科学阅读/分析泛化能力 | 中 | 中 | 中 | 中 | 中 | 中 | 低到中：安装数低，作为概念参考 |
| `nature-reader` | local `.agents/skills` | 强，全文 source-map first | 强，保留上下文 | 强，因不降级为 summary | 强，要求 source anchors | 中，需要额外方法解释器 | 中，能保留图表位置 | 中 | 直接参考：source-grounded full-paper reader |

### 3.2 Research / Literature Review / Gap Discovery

| Skill | Repository | 背景提取 | 动机提取 | 研究空白 | 核心贡献 | 方法有效性 | 实验解读 | 故事线 | 迁移判断 |
|---|---|---|---|---|---|---|---|---|---|
| `research` | `hyperb1iss/hyperskills` | 强，通用调研 | 中 | 中 | 中 | 弱 | 弱 | 弱 | 适合补充外部背景，不适合单篇深读 |
| `researcher` | `dangeles/claude` | 中 | 中 | 中 | 中 | 弱 | 弱 | 中 | 可参考 research agent 角色定义 |
| `deep-research` | `nateberkopec/dotfiles` | 强 | 中 | 中 | 中 | 弱 | 弱 | 中 | 可用于背景和 prior work 扩展 |
| `cowork-multi-agent-research` | `cowork-os/cowork-os` | 中 | 中 | 中 | 中 | 中 | 中 | 中 | 可参考多 agent 分工 |
| `literature-review` | `affaan-m/everything-claude-code` | 强 | 强 | 强 | 中 | 弱 | 弱 | 中 | 高价值：迁移 gap matrix / related work map |
| `literature-review` | `getcompanion-ai/feynman` | 强，面向解释 | 强，强调“讲给别人听” | 中 | 中 | 中 | 中 | 强 | 高价值：Audience-first/Feynman explanation |
| `lit-review` | `thinkingwithagents/skills` | 强 | 中 | 强 | 中 | 弱 | 弱 | 中 | 可用于 related-work contrast |
| `research-methodology` | `itallstartedwithaidea/agent-skills` | 中 | 中 | 中 | 中 | 中 | 中 | 中 | 可参考研究问题与方法论拆解 |
| `research-intelligence` | `spitoglou/fabric-claude-skills` | 中 | 中 | 中 | 中 | 弱 | 弱 | 中 | 可参考 insight extraction |
| `research-lit` | local ARIS | 强，支持本地/网页/学术源 | 强，结合已有文献 | 强，能找 related work 与空白 | 中 | 弱 | 弱 | 中 | 直接参考：本地文献库优先、外部搜索补空白 |
| `comm-lit-review` | local ARIS | 强，通信/网络领域优先 IEEE/ACM | 强，能构造领域背景 | 强，按 venue/年份/主题梳理 | 中 | 弱 | 弱 | 中 | 对 TSN/DetNet 项目非常有用 |
| `novelty-check` | local ARIS | 中 | 强，围绕 idea 的必要性 | 强，检查是否已有工作 | 强，检查技术 claim 新颖性 | 中 | 弱 | 中 | 高价值：Research Gap / Novelty Auditor |

### 3.3 Motivation / Insight / Storytelling

| Skill | Repository | 背景提取 | 动机提取 | 研究空白 | 核心贡献 | 方法有效性 | 实验解读 | 故事线 | 迁移判断 |
|---|---|---|---|---|---|---|---|---|---|
| `insight-extraction` | `oimiragieo/agent-studio` | 中 | 中 | 中 | 中 | 中 | 中 | 中 | 可参考 insight schema，但需复核实现 |
| `insightly` | `membranedev/application-skills` | 中 | 中 | 中 | 中 | 弱 | 弱 | 中 | 偏通用洞察提取，低到中 |
| `drive-motivation` | `wondelai/skills` | 弱 | 强，但偏个人/行为动机 | 弱 | 弱 | 弱 | 弱 | 中 | 不直接迁移；可借鉴“动因链”结构 |
| `storytelling` | `ghaida/intent` | 弱 | 中 | 弱 | 中 | 弱 | 弱 | 强 | 可参考叙事结构，但需科研化 |
| `communication-storytelling` | `lyndonkl/claude` | 弱 | 中 | 弱 | 中 | 弱 | 弱 | 强 | 可参考听众视角表达 |
| `data-storyteller` | `jmsktm/claude-settings` | 弱 | 弱 | 弱 | 中 | 弱 | 强 | 强 | 对实验结果讲故事有价值 |
| `grad-narrative` | `asgard-ai-platform/skills` | 中 | 强 | 中 | 中 | 弱 | 弱 | 强 | 可参考研究生/开题式研究叙事 |
| `paper-talk` | local ARIS | 中 | 中 | 中 | 中 | 中 | 中 | 强 | 适合最终 presentation story，但不是理解引擎本体 |

### 3.4 Method Explanation

| Skill | Repository | 背景提取 | 动机提取 | 研究空白 | 核心贡献 | 方法有效性 | 实验解读 | 故事线 | 迁移判断 |
|---|---|---|---|---|---|---|---|---|---|
| `method-section-explainer` | `a-green-hand-jack/ml-research-skills` | 弱 | 弱 | 弱 | 中 | 强 | 弱 | 中 | 必迁移思路：方法拆成 assumptions / inputs / mechanism / outputs / why effective |
| `code-explanation` | `nickcrew/claude-ctx-plugin` | 不适用 | 不适用 | 不适用 | 弱 | 中，偏代码解释 | 弱 | 弱 | 仅当论文附带代码时参考 |
| `code-explanation` | `joaquimscosta/arkhe-claude-plugins` | 不适用 | 不适用 | 不适用 | 弱 | 中，偏代码解释 | 弱 | 弱 | 低优先级 |
| `java-refactoring-extract-method` | `github/awesome-copilot` | 不适用 | 不适用 | 不适用 | 不适用 | 不适用 | 不适用 | 不适用 | 不迁移，检索噪声 |

### 3.5 Experiment / Result Interpretation

| Skill | Repository | 背景提取 | 动机提取 | 研究空白 | 核心贡献 | 方法有效性 | 实验解读 | 故事线 | 迁移判断 |
|---|---|---|---|---|---|---|---|---|---|
| `statistical-analyst` | `alirezarezvani/claude-skills` | 弱 | 弱 | 弱 | 弱 | 中 | 强，统计/显著性/数据解释 | 中 | 可迁移到 Experiment Interpreter |
| `results-report` | `galaxy-dawn/claude-scholar` | 弱 | 弱 | 弱 | 中 | 中 | 强，结果报告 | 中 | 高价值：结果页不能只复述图表 |
| `experiment-report-writer` | `a-green-hand-jack/ml-research-skills` | 弱 | 弱 | 弱 | 中 | 中 | 强 | 中 | 可参考实验设置/指标/结论结构 |
| `analytics-interpretation` | `nicepkg/ai-workflow` | 弱 | 弱 | 弱 | 弱 | 中 | 中到强 | 中 | 可参考 trend -> implication |
| `result-to-claim` | local ARIS | 弱 | 弱 | 中 | 强，判断结果支持什么 claim | 强，反推机制是否被证实 | 强，区分 support/partial/no | 中 | 必迁移：Result-to-Claim Matrix |
| `experiment-audit` | local ARIS | 弱 | 弱 | 弱 | 中 | 中 | 强，检查实验完整性/诚信/范围 | 弱 | 高价值：防止实验解读过度 |
| `paper-claim-audit` | local ARIS | 弱 | 弱 | 弱 | 强，核对数字与 claim | 中 | 强，检查 caption/table/scope overclaim | 弱 | 高价值：PPT claim 也应做 evidence audit |

### 3.6 Professor Review / Critical Reading

| Skill | Repository | 背景提取 | 动机提取 | 研究空白 | 核心贡献 | 方法有效性 | 实验解读 | 故事线 | 迁移判断 |
|---|---|---|---|---|---|---|---|---|---|
| `professor-synapse` | `profsynapse/professor-synapse` | 中 | 中 | 中 | 中 | 中 | 中 | 中 | 通用专家协调角色，可参考但需科研化 |
| `nature-reviewer` | local `.agents/skills` | 强，评估 broad-interest | 强，评估 significance | 强，指出 missing evidence | 强，审稿式判断贡献强弱 | 强，评估 technical soundness | 强，指出 evidence 不足 | 中 | 必迁移：Professor Reviewer |
| `research-review` | local ARIS | 强，基于完整 briefing | 强 | 强 | 强 | 强，找 logical gaps | 强，找 missing experiments | 强 | 必迁移：xhigh critical review loop |
| `kill-argument` | local ARIS | 中 | 强，暴露动机/范围攻击点 | 强，找最致命弱点 | 强，攻击 headline claim | 强，找方法/假设漏洞 | 中 | 强，反向强化故事线 | 高价值：Adversarial Understanding |

## 4. 当前 Skill 的论文理解短板

当前 `paper-to-group-meeting-ppt-release` 已经有较完整的展示层：

```text
PDF -> paper_model -> storyboard -> visual_plan -> deck_model -> HTML/PPTX -> validators
```

但理解层仍然薄弱。具体看 `scripts/generate_academic_presentation.py`，核心抽取主要依赖：

```python
first_matching(sentences, keywords)
```

这意味着当前系统的理解大多来自关键词命中，而不是研究逻辑推理。

### 4.1 背景介绍过于表面

当前做法：

- 从摘要、引言中找包含 `traffic planning`、`NP-hard` 等关键词的句子。
- 直接把这些句子压缩进 background slide。

缺少能力：

- 领域背景层级：
  - 这个领域长期解决什么问题？
  - 主流方法是什么？
  - 为什么现在变得困难？
- 背景压力链：
  - application pressure -> technical requirement -> planning bottleneck。
- 背景与本文问题之间的因果连接。

需要引入：

- Domain Primer Builder
- Background Causal Map
- Related Work Context Builder

### 4.2 动机分析不深入

当前做法：

- 抽取引言中看起来像 motivation 的句子。

缺少能力：

- 区分：
  - surface problem：论文显式说的问题
  - deep tension：为什么已有范式失效
  - research opportunity：为什么现在可以换一种方法
- 构造动机链：

```text
Existing paradigm works under assumption A
-> target setting violates A
-> direct extension causes bottleneck B
-> therefore a new representation / method is needed
```

需要引入：

- Motivation Chain Extractor
- Assumption-Break Detector
- Pain Point Classifier

### 4.3 研究空白识别不足

当前做法：

- 单篇论文内部抽取 related work 信号。

缺少能力：

- 没有构建 prior work taxonomy。
- 没有比较不同 prior work 的假设、能力、局限。
- 没有识别：
  - studied enough
  - partially solved
  - clearly missing
  - paper-specific gap

需要引入：

- Related Work Matrix
- Gap Type Classifier
- Novelty / Prior-art Auditor

### 4.4 贡献总结不准确

当前做法：

- 从贡献段、摘要中摘句子。

缺少能力：

- 贡献类型分类：
  - problem formulation
  - algorithm
  - system
  - theory/model
  - empirical finding
  - dataset/benchmark
- 贡献强度判断：
  - incremental
  - reframing
  - enabling
  - empirically stronger
  - theoretically grounded
- 贡献证据绑定：
  - 哪个实验/定理/图证明哪个贡献？

需要引入：

- Contribution Card Extractor
- Claim-Evidence Graph
- Novelty Strength Estimator

### 4.5 方法解释停留在结构层面

当前做法：

- 方法页大多解释“先做 A，再做 B，再做 C”。

缺少能力：

- 方法为什么可能有效：
  - 它改变了什么表示？
  - 它减少了什么耦合？
  - 它利用了什么性质？
  - 它牺牲了什么？
- 方法适用条件：
  - assumptions
  - inputs / outputs
  - invariants
  - complexity
  - failure modes
- 方法和问题之间的因果链：

```text
Problem bottleneck
-> Method mechanism
-> Reduced difficulty / improved search / better guarantee
-> Expected result
```

需要引入：

- Method Mechanism Model
- Assumption / Invariant Extractor
- Why-Effective Reasoner

### 4.6 实验结果只是复述图表

当前做法：

- 找到 evaluation 句子，提取 runtime/memory 等关键词。
- 结果页容易写成“论文比较了 X 和 Y，结果更好”。

缺少能力：

- 每个实验回答什么 research question？
- baseline 是否公平？
- metric 对应哪个 claim？
- 趋势说明机制有效，还是只说明实现快？
- 负结果/异常点/方差/规模边界说明什么？
- 结果能支持多强的 claim？

需要引入：

- Experiment Card Extractor
- Result-to-Claim Matrix
- So-What Interpreter
- Evidence Scope Auditor

### 4.7 缺少教授式理解审查

当前 reviewer 更多检查结构与布局，缺少真正的科研审查：

- 这个背景是否太泛？
- 这个动机是否只是作者自说自话？
- 这个贡献是否被夸大？
- 方法有效性的解释是否只是流程描述？
- 实验是否真的验证核心 claim？
- 哪些点会被老教授追问？

需要引入：

- Professor Understanding Review
- Hostile Reviewer / Kill Argument
- Claim Scope Auditor

## 5. Research Understanding Engine 设计方案

建议把当前系统升级为：

```text
PDF
-> Source Map
-> Research Understanding Engine
-> Story Brief
-> Visual Plan
-> Deck Generation
```

也就是说，PPT 生成不再直接消费 `paper_analysis.md` 或关键词句子，而是消费研究理解引擎输出。

### 5.1 输入

```text
paper.pdf
optional supplementary materials
optional code
optional author slides
optional local related papers
optional web / Semantic Scholar / OpenAlex context
```

### 5.2 输出

建议新增以下中间文件：

| 文件 | 作用 |
|---|---|
| `source_map.json` | 页码、章节、图表、公式、算法、caption、引用位置 |
| `term_ledger.json` | 核心术语、中英文、缩写、首次出现位置 |
| `domain_primer.md` | 领域背景解释，给未读论文的人读 |
| `motivation_chain.json` | 背景 -> 痛点 -> 旧方法失效 -> 新需求 |
| `related_work_matrix.json` | prior work 的方法、假设、局限、与本文差异 |
| `gap_analysis.json` | 研究空白类型与证据 |
| `contribution_cards.json` | 每个贡献的类型、强度、证据、边界 |
| `method_model.json` | 方法输入、输出、模块、机制、假设、不变量 |
| `why_effective.md` | 方法为什么可能有效的因果解释 |
| `experiment_cards.json` | 每个实验的问题、设置、baseline、metric、结果、结论 |
| `result_to_claim_matrix.json` | 每个结果支持/不支持/部分支持哪个 claim |
| `limitation_risks.md` | 作者局限 + reviewer 可能质疑 |
| `research_story_brief.md` | Why / What / How / Why Effective / How Verified |
| `understanding_review.md` | Professor Reviewer 对理解质量的审查 |

### 5.3 核心 Agent

#### A. Source Map Builder

职责：

- 解析 PDF 结构。
- 建立章节、段落、图表、算法、公式、引用的 source anchors。
- 所有理解输出必须能回溯到 source map。

迁移参考：

- `nature-reader`
- `paper-claim-audit`

#### B. Domain Primer Builder

回答：

```text
这个领域在解决什么长期问题？
为什么这个问题重要？
听众需要知道哪些术语和背景？
```

输出：

- domain context
- key terms
- standard pipeline
- common baselines
- field assumptions

迁移参考：

- `research-lit`
- `comm-lit-review`
- `nature-reader`

#### C. Motivation Chain Extractor

回答：

```text
为什么作者要做这个工作？
现有范式哪里不适合本文场景？
真正的 tension 是什么？
```

输出结构：

```json
{
  "known_context": "...",
  "prevailing_approach": "...",
  "assumption_that_breaks": "...",
  "observed_bottleneck": "...",
  "research_need": "...",
  "source_evidence": [...]
}
```

迁移参考：

- `analyzing-research-papers`
- `literature-review`
- `drive-motivation` 的动因链思路

#### D. Gap Matrix Builder

回答：

```text
已有工作解决了什么？
哪些问题已经充分研究？
本文真正填补的是哪个 gap？
```

输出结构：

| Prior Work Type | Solves | Assumes | Fails When | Paper's Delta |
|---|---|---|---|---|

迁移参考：

- `literature-review`
- `comm-lit-review`
- `novelty-check`

#### E. Contribution Card Extractor

回答：

```text
本文贡献到底是什么？
是方法、建模、系统、理论，还是实验发现？
每个贡献由什么证据支持？
贡献边界是什么？
```

输出结构：

```json
{
  "contribution": "...",
  "type": "problem_formulation | algorithm | system | theory | empirical",
  "novelty_basis": "...",
  "evidence": ["Fig. 7", "Sec. V"],
  "scope": "...",
  "possible_overclaim": "..."
}
```

迁移参考：

- `paper-claim-audit`
- `nature-reviewer`
- `novelty-check`

#### F. Method Mechanism Model

回答：

```text
方法如何工作？
为什么这个机制能解决前面的问题？
它依赖什么假设？
它的失败模式是什么？
```

输出结构：

```json
{
  "inputs": [],
  "outputs": [],
  "modules": [],
  "core_mechanism": "...",
  "assumptions": [],
  "invariants": [],
  "why_effective": "...",
  "complexity_or_scalability": "...",
  "failure_modes": []
}
```

迁移参考：

- `method-section-explainer`
- `research-review`

#### G. Experiment Interpreter

回答：

```text
每个实验到底验证什么？
实验结果支持哪个 claim？
结果有没有超出证据范围？
```

输出结构：

```json
{
  "experiment_id": "Fig. 9",
  "research_question": "...",
  "setup": "...",
  "baselines": [],
  "metrics": [],
  "main_observation": "...",
  "supports_claim": "...",
  "does_not_support": "...",
  "caveats": [],
  "so_what": "..."
}
```

迁移参考：

- `results-report`
- `experiment-report-writer`
- `statistical-analyst`
- `result-to-claim`
- `experiment-audit`

#### H. Research Story Synthesizer

把前面所有理解压缩成面向听众的五问：

```text
Why:
为什么这个问题重要？

What:
本文解决什么具体问题？

How:
本文如何解决？

Why Effective:
为什么这个方法可能有效？

How Verified:
实验如何证明它有效，证明到什么程度？
```

输出：

- `research_story_brief.md`
- `story_spine.json`

迁移参考：

- `getcompanion-ai/feynman/literature-review`
- `communication-storytelling`
- `paper-talk`

#### I. Professor Understanding Reviewer

职责不是评价 PPT，而是评价“理解是否站得住”。

评分维度：

1. Background Depth
2. Motivation Depth
3. Gap Accuracy
4. Contribution Accuracy
5. Method Causal Explanation
6. Experiment Interpretation
7. Claim-Evidence Fidelity
8. Reviewer Question Readiness

输出：

```text
KEEP
REMOVE
ADD
MODIFY
UNSUPPORTED CLAIMS
LIKELY PROFESSOR QUESTIONS
```

迁移参考：

- `nature-reviewer`
- `research-review`
- `kill-argument`
- `paper-claim-audit`

## 6. 推荐的 Engine 数据流

```text
1. Parse Source
   PDF -> source_map.json + term_ledger.json

2. Understand Context
   source_map -> domain_primer.md
   source_map + related work -> related_work_matrix.json

3. Build Research Logic
   domain_primer + intro + related_work -> motivation_chain.json
   related_work_matrix -> gap_analysis.json
   abstract + intro + conclusion -> contribution_cards.json

4. Explain Mechanism
   method sections + equations + figures -> method_model.json
   method_model + gap_analysis -> why_effective.md

5. Interpret Evidence
   experiments + figures + tables -> experiment_cards.json
   experiment_cards + contribution_cards -> result_to_claim_matrix.json

6. Review Understanding
   all artifacts -> understanding_review.md

7. Feed Presentation
   research_story_brief.md + visual_plan -> deck_model
```

## 7. Quality Gates

后续生成 PPT 前，Research Understanding Engine 必须通过以下 gates。

### Gate 1: Why Gate

必须回答：

- 领域长期问题是什么？
- 为什么这个问题现在仍然难？
- 本文场景与已有假设的冲突是什么？

失败信号：

- 背景页只有“该领域很重要”。
- 只复述 abstract。

### Gate 2: Gap Gate

必须回答：

- 至少 2-4 类已有方法是什么？
- 它们分别解决了什么？
- 它们为什么不能直接解决本文问题？

失败信号：

- “已有方法不够好”但没有具体方法类别。
- 没有 assumption / limitation 对比。

### Gate 3: Contribution Gate

必须回答：

- 每个贡献是什么类型？
- 新在哪里？
- 由什么证据支持？
- 边界是什么？

失败信号：

- 把“作者做了实验”当贡献。
- 把所有贡献都写成“提出了一种方法”。

### Gate 4: Method Gate

必须回答：

- 方法输入/输出是什么？
- 关键机制是什么？
- 为什么能解决 gap？
- 依赖什么假设？
- 什么时候可能失败？

失败信号：

- 只画 pipeline。
- 不能解释 why effective。

### Gate 5: Experiment Gate

必须回答：

- 每个实验验证哪个 claim？
- baseline/metric 是否对应这个 claim？
- 结果支持到什么程度？
- 有什么未验证？

失败信号：

- 只说“结果更好”。
- 没有 so what。
- 没有 evidence scope。

### Gate 6: Professor Gate

必须回答：

- 老教授最可能问哪 5 个问题？
- 哪个贡献最可能被质疑？
- 哪个实验最可能被认为不充分？
- 哪句话可能是 overclaim？

失败信号：

- reviewer 只评价排版。
- 没有 unsupported / weak / not assessable 区分。

## 8. 对当前项目的下一步建议

### P0: 先替换关键词式理解

当前 `generate_academic_presentation.py` 的 `first_matching` 只能作为 fallback。

应新增：

```text
scripts/build_research_understanding.py
```

先输出：

- `research_understanding.json`
- `research_story_brief.md`
- `result_to_claim_matrix.json`
- `understanding_review.md`

然后 PPT 入口读取这些文件，而不是直接从 PDF 句子生成 slide。

### P1: 加入理解审查

在 `refine_presentation_loop.py` 之前增加：

```text
understanding_review_loop.py
```

它先审查：

- 背景是否深
- 动机是否成立
- 贡献是否准确
- 方法有效性是否解释清楚
- 实验解释是否支持 claim

只有 understanding review 通过，才进入 slide generation。

### P2: 接入 literature context

对 TSN / DetNet 这类科研项目，单篇论文理解不足以判断 gap。

应允许输入：

```text
--related-papers folder
--academic-search notes
--local-literature-index
```

用于生成：

- related_work_matrix
- gap_analysis
- novelty_risk

### P3: 引入 adversarial professor reviewer

在最终生成前运行：

```text
hostile_reviewer_questions.md
```

它应模拟老教授追问：

- 这个问题为什么重要？
- 这个 gap 真的是 gap 吗？
- 方法只是换个表述吗？
- 实验是否证明了核心机制？
- 结论是否超出证据？

## 9. 最终架构建议

目标架构应改为：

```text
PDF
-> Research Understanding Engine
   -> Domain Primer
   -> Motivation Chain
   -> Gap Matrix
   -> Contribution Cards
   -> Method Mechanism Model
   -> Experiment Cards
   -> Result-to-Claim Matrix
   -> Professor Understanding Review
-> Presentation Agent
   -> Storyboard
   -> Visual Plan
   -> HTML/PPTX
```

一句话：

```text
先把论文读懂，再把理解讲清楚。
```

当前 skill 已经比较接近“讲清楚”的工程框架，下一步真正要补的是“读懂”的研究推理框架。

## 10. 不建议迁移的检索噪声

本轮 find skill 也检索到了若干不适合迁移的结果：

- `java-refactoring-extract-method`：代码重构，不是论文方法解释。
- `copilotkit-contribute`、`nvidia/contributing`、`mindfold/contribute`：开源贡献流程，不是论文贡献提取。
- `user-personas`、`user-segmentation`：PM/产品分析，不适合科研论文理解。
- `anthropics/claude-for-legal/*`：法律 workflow，不适合 Professor Review。
- `datasheet-interpreter`：硬件 datasheet 场景，和科研实验解释相距较远。

这些结果说明搜索词必须围绕 `paper`, `research`, `method`, `experiment`, `claim`, `reviewer` 进一步收窄。

