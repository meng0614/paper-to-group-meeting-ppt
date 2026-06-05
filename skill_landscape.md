# Skill Landscape: Academic Presentation Agent

生成日期：2026-06-05

项目：`paper-to-group-meeting-ppt-release`

阶段：Skill Evolution 调研与架构设计

本阶段只做调研、比较和架构设计，不修改现有代码。

## 1. 调研目标

当前项目不应继续定位为简单的 `PDF -> PPT` 转换工具，而应升级为一个通用的 Academic Presentation Agent：

```text
PDF / Supplementary Materials
-> Paper Understanding
-> Research Story Design
-> Visual-first Slide Planning
-> Concept / Architecture / Scientific Visualization
-> HTML / PPTX Presentation Generation
-> Professor Review
-> Iterative Optimization
```

最终输出应接近 SIGCOMM、NSDI、INFOCOM、Google Research Talk、Microsoft Research Talk 的学术报告风格，而不是传统论文摘要 PPT。

## 2. 调研方法

本次调研使用了三类来源：

1. 目标 Skill 仓库
   - `helloianneo/ian-xiaohei-illustrations`
   - `yaojingang/yao-open-skills/skills/yao-expert-skill`
2. 本地已安装科研相关 skills
   - `paper-to-group-meeting-ppt`
   - `nature-paper2ppt`
   - `paper-slides`
   - `slides-polish`
   - `academic-plotting`
   - `mermaid-diagram`
   - `nature-reviewer`
3. 主动使用 find skill 检索的候选 skill
   - 原始检索结果保存于：
     `C:\Users\30430\Documents\research\outputs\skill_evolution_research\raw_skill_search\`
   - 检索词包括：
     `PDF PPT`, `PDF HTML Presentation`, `Research Agent`, `Literature Review Agent`,
     `Paper Understanding Agent`, `Diagram Generator`, `Architecture Diagram Generator`,
     `Scientific Visualization`, `Slide Designer`, `Presentation Agent`,
     `Academic Writing Agent`, `Professor Reviewer`, `paper reviewer`,
     `presentation review`, `critique`, `academic presentation`。

说明：本轮网络访问 GitHub raw/API 时存在连接不稳定，因此对外部 skill 的细节判断主要基于公开 skill metadata、仓库页面摘要、find skill 检索结果和可见仓库说明。正式迁移前应逐个安装到隔离目录做代码级复核。

## 3. 重点 Skill 深入分析

### 3.1 helloianneo/ian-xiaohei-illustrations

| 字段 | 分析 |
|---|---|
| Skill Name | `ian-xiaohei-illustrations` |
| Repository | `https://github.com/helloianneo/ian-xiaohei-illustrations` |
| 解决的问题 | 把中文文章、帖子、方法论、流程、结构、隐喻、观点等抽象概念转化为“正文配图”或 shot list。 |
| 核心能力 | 抽象概念提炼、认知锚点设计、视觉隐喻选择、16:9 白底手绘风格插图、少量颜色批注、为文章段落生成配图建议。 |
| 实现方式 | 以 prompt / skill workflow 为主，先从文本中抽取观点，再生成视觉 brief、构图、元素、风格约束和图像生成提示。 |
| 是否适合迁移 | 高，但不应直接迁移其具体“小黑怪诞”风格。更适合迁移其“抽象概念 -> 视觉隐喻 -> 构图 brief -> 视觉 QA”的工作流。 |
| 迁移成本 | 中。需要把文章插图语境改造成学术报告语境，把“趣味插图”约束改成“学术概念图 / 机制图 / 场景图”。 |
| 预期收益 | 显著提升 Concept Illustration 能力。尤其适合 Background、Problem、Challenge、Key Idea、Takeaway 页，让 PPT 不再只是文字摘要。 |

#### 对 Academic Presentation Agent 的启发

1. 每页先确定一个 cognitive anchor：观众 5 秒内应该记住什么。
2. 复杂论文概念先转成 visual metaphor，而不是直接转成 bullets。
3. 生成视觉主体前先写 visual brief：
   - 主题
   - 观众应看到的冲突或关系
   - 核心对象
   - 空间布局
   - 强调元素
   - 禁止元素
4. 需要区分三类视觉：
   - 解释性概念图：解释为什么有这个问题。
   - 机制性流程图：解释方法如何工作。
   - 证据性数据图：证明方法是否有效。
5. 对本项目而言，推荐迁移的是“构图逻辑”和“图示生成流程”，不是卡通化画风。

### 3.2 yaojingang/yao-open-skills/yao-expert-skill

| 字段 | 分析 |
|---|---|
| Skill Name | `yao-expert-skill` |
| Repository | `https://github.com/yaojingang/yao-open-skills/tree/main/skills/yao-expert-skill` |
| 解决的问题 | 把某一领域的知识、术语、边界、判断标准和反馈流程沉淀为可复用的专家型 skill。 |
| 核心能力 | 专家视角建模、结构化评审、批判性反馈、知识边界声明、术语卡、事实/推断/假设/未知区分、多轮改进。 |
| 实现方式 | 以结构化 prompt 和评审模板为主，强调先建立领域事实基座，再做专家判断；输出时区分支持、薄弱、不确定和不可评估内容。 |
| 是否适合迁移 | 高。Professor Reviewer、Discriminator、Evidence Checker、Iteration Controller 都可参考。 |
| 迁移成本 | 低到中。可先迁移评审维度和 KEEP / REMOVE / ADD / MODIFY 输出结构，再逐步加入领域自适应专家画像。 |
| 预期收益 | 显著提升科学准确性和多轮优化稳定性，避免“看起来漂亮但讲错论文”的问题。 |

#### 对 Academic Presentation Agent 的启发

1. Reviewer 不能只评价美观，还必须评价：
   - 论文事实是否准确
   - 图表趋势是否忠实
   - 方法是否被误解
   - 实验结论是否被夸大
   - 局限性是否被隐藏
2. 每轮修改必须有明确原因，写入 `improvement_history.md`。
3. 审查输出应强制结构化：
   - KEEP：保留什么
   - REMOVE：删掉什么
   - ADD：补充什么
   - MODIFY：如何改
4. 必须区分：
   - Paper fact
   - Agent inference
   - Visual simplification
   - Unverified claim
5. 对跨学科论文，应先建立 domain primer，再生成 slides。

## 4. 本地已安装 Skill 可复用性

| Skill Name | Repository / Path | 解决的问题 | 核心能力 | 实现方式 | 是否适合迁移 | 迁移成本 | 预期收益 |
|---|---|---|---|---|---|---|---|
| `paper-to-group-meeting-ppt` | `.agents/skills/paper-to-group-meeting-ppt` | 论文到组会 PPT 的端到端流程 | PDF 解析、visual storyboard、HTML/PPTX、layout report、review loop | 本项目当前 skill / 脚本集合 | 直接作为基线 | 低 | 保留现有资产，避免重写 |
| `nature-paper2ppt` | `.agents/skills/nature-paper2ppt` | Nature 风格论文转中文 PPT | 论文类型判断、分章节讲解、图表优先、speaker notes、自评 | Skill workflow + 参考文件 | 高，参考实现 | 中 | 增强 paper type routing 和讲稿质量 |
| `paper-slides` | ARIS skills-codex | 从论文生成 conference talk slides | talk 类型、时长约束、outline checkpoint、slide count planning | LaTeX / Beamer / PPTX 工作流 | 中，高价值参考 | 中 | 帮助从“论文结构”切换为“报告结构” |
| `slides-polish` | ARIS skills-codex | 已生成 slides 的视觉和排版打磨 | slide inventory、rendered preview、逐页审查、版本化输出 | 检查 + 修改循环 | 高，参考实现 | 中 | 支撑 Layout Validator 和 Visual Reviewer |
| `academic-plotting` | `.agents/skills/orchestra-academic-plotting` | 学术图表和系统图生成 | 图表类型选择、系统组件/关系抽取、publication-quality plotting | Python plotting / diagram prompt | 高，参考实现 | 中 | 支撑 Scientific Visualization 和 Architecture Diagram |
| `mermaid-diagram` | ARIS skills-codex | 生成并验证 Mermaid 图 | 流程图、架构图、时序图、状态图、语法验证、视觉评分 | Mermaid CLI + strict review | 高，可部分直接复用 | 低到中 | 快速生成可编辑概念图和架构图 |
| `nature-reviewer` | `.agents/skills/nature-reviewer` | 模拟高标准 reviewer 评审 | 事实基座、3 reviewer reports、cross-review synthesis、非臆造约束 | 结构化 reviewer workflow | 高，参考实现 | 中 | 强化 Professor Reviewer 的科学性审查 |
| `figure-description` | ARIS skills-codex | 技术图像组件识别和说明 | 图像组件识别、连接关系、结构化说明 | 图像读取 + component mapping | 中，参考实现 | 中 | 帮助理解论文图示，但需从专利语境迁移到论文语境 |

## 5. find Skill 检索到的外部候选

迁移适配等级：

- 直接复用：可安装后直接作为子流程调用或轻量封装。
- 参考实现：不直接依赖，但借鉴其 prompt、流程、QA 或数据结构。
- 低优先级：与目标相关但收益有限。
- 不建议迁移：偏离 Academic Presentation Agent 核心目标。

### 5.1 PDF / PPT / HTML Presentation

| Skill Name | Repository | 解决的问题 | 核心能力 | 实现方式 | 是否适合迁移 | 迁移成本 | 预期收益 |
|---|---|---|---|---|---|---|---|
| `ai-ppt-generate` | `skills.volces.com` | 通用 AI PPT 生成 | 自动生成 PPT 内容与版式 | 外部 skill / 服务式能力 | 参考实现 | 中 | 了解通用 PPT 自动化边界 |
| `glmv-pdf-to-ppt` | `modelscope.cn` | PDF 转 PPT | PDF 内容抽取、PPT 生成 | 模型驱动转换 | 参考实现 | 中 | 可参考 PDF-to-slide 基线 |
| `html-ppt` | `nexu-io/open-design` | HTML 生成 PPT | HTML slides、网页式排版 | HTML/CSS 渲染 | 高，参考实现 | 中 | 与当前 HTML -> PPTX 方向高度相关 |
| `glmv-pdf-to-ppt` | `zai-org/glm-skills` | PDF 转 PPT | PDF 解析和版式生成 | GLM skill workflow | 参考实现 | 中 | 可作为备选 PDF 转换能力 |
| `ppt-compress` | `skills.volces.com` | PPT 压缩 | 降低文件体积 | 文件处理 | 低优先级 | 低 | 仅用于发布阶段 |
| `html-ppt` | `skills.volces.com` | HTML 转 PPT | 网页到演示文稿 | HTML render / conversion | 参考实现 | 中 | 有助于 HTML presentation pipeline |
| `slide-creator` | `starchild-ai-agent/official-skills` | 从内容创建 slides | slide 结构、版式、内容生成 | Skill workflow | 高，参考实现 | 中 | 可借鉴 slide model 和页面生成流程 |
| `publish-to-pages` | `github/awesome-copilot` | 发布 HTML 到 GitHub Pages | 静态站点部署 | GitHub Pages workflow | 低优先级 | 低 | 可用于 demo 发布，不是核心生成能力 |
| `ln-150-presentation-creator` | `levnikolaevich/claude-code-skills` | 创建演示文稿 | 内容组织、slide creation | Prompt workflow | 参考实现 | 中 | 可参考 presentation creator prompt |
| `elegant-reports` | `jdrhyne/agent-skills` | 生成美观 HTML 报告 | HTML 报告、排版、视觉层次 | HTML/CSS 模板 | 高，参考实现 | 中 | 可增强 HTML report 美观度 |
| `html-presentation` | `mathews-tom/praxis-skills` | HTML 演示文稿 | Section-based presentation | HTML/CSS | 高，参考实现 | 中 | 与本项目 HTML 输出直接相关 |
| `html-presentation-beautifier` | `within-7/minto-plugin-tools` | 美化 HTML presentation | 视觉风格、布局优化 | HTML/CSS polish | 高，参考实现 | 低到中 | 可作为 Visual Designer 参考 |

### 5.2 Research / Literature / Paper Understanding

| Skill Name | Repository | 解决的问题 | 核心能力 | 实现方式 | 是否适合迁移 | 迁移成本 | 预期收益 |
|---|---|---|---|---|---|---|---|
| `research` | `hyperb1iss/hyperskills` | 通用研究任务 | 搜索、归纳、证据组织 | Research workflow | 参考实现 | 中 | 强化文献背景和 related work |
| `research-codebase` | `flora131/atomic` | 代码库研究 | 代码结构理解、定位 | Code research workflow | 低优先级 | 中 | 对补充材料代码有用 |
| `paw-ps-research` | `pawbytes/skill-suites` | 研究支持 | 信息收集与分析 | Skill workflow | 低优先级 | 中 | 可作为搜索流程参考 |
| `researcher` | `dangeles/claude` | 研究员代理 | 多源调研、总结 | Prompt workflow | 参考实现 | 中 | 可借鉴 research agent 角色定义 |
| `cowork-multi-agent-research` | `cowork-os/cowork-os` | 多智能体研究 | 多 agent 协作 | Multi-agent workflow | 参考实现 | 高 | 对后续 Generator/Reviewer 协作有启发 |
| `deep-research` | `nateberkopec/dotfiles` | 深度调研 | 搜索、引用、长文总结 | Research workflow | 参考实现 | 中 | 强化背景页证据来源 |
| `literature-review` | `affaan-m/everything-claude-code` | 文献综述 | 文献筛选、主题归纳、研究空白 | Literature review workflow | 高，参考实现 | 中 | Paper Understanding 和背景补强 |
| `literature review` | `jmsktm/claude-settings` | 文献综述 | 综述结构化输出 | Prompt workflow | 参考实现 | 低 | 可借鉴输出模板 |
| `literature-review` | `ovachiever/droid-tings` | 文献综述 | 归纳、比较、引用 | Prompt workflow | 参考实现 | 中 | 低成本增强 review logic |
| `literature-review` | `getcompanion-ai/feynman` | Feynman 式文献理解 | 解释、提问、自测 | Teaching workflow | 高，参考实现 | 中 | 支撑 Audience First |
| `lit-review` | `thinkingwithagents/skills` | 文献综述 | related work mapping | Prompt workflow | 参考实现 | 中 | 可用于 paper context |
| `literature-review` | `dsebastien/ai-skill-scholar` | 学术综述 | 学术搜索、综述结构 | Prompt workflow | 参考实现 | 中 | 强化背景和差异化 |
| `chat-with-arxiv` | `qodex-ai/ai-agent-skills` | 与 arXiv 论文交互 | 论文问答、摘要 | PDF / arXiv workflow | 参考实现 | 中 | 可作为 paper QA 子模块 |
| `method-section-explainer` | `a-green-hand-jack/ml-research-skills` | 解释方法章节 | 方法拆解、机制解释 | Prompt workflow | 高，参考实现 | 低到中 | 直接增强 Method Details |
| `agentic-paper-digest-skill` | `matanle51/agentic-paper-digest-skill` | 论文消化 | 摘要、贡献、方法、实验 | Agentic digest | 参考实现 | 中 | 可作为 Paper Understanding baseline |

### 5.3 Diagram / Architecture / Visualization

| Skill Name | Repository | 解决的问题 | 核心能力 | 实现方式 | 是否适合迁移 | 迁移成本 | 预期收益 |
|---|---|---|---|---|---|---|---|
| `baoyu-diagram` | `jimliu/baoyu-skills` | 生成图示 | diagram prompt、视觉结构 | Diagram workflow | 高，参考实现 | 中 | 增强概念图生成 |
| `generating-mermaid-diagrams` | `forcedotcom/sf-skills` | 生成 Mermaid 图 | Mermaid syntax、流程图、架构图 | Mermaid | 高，可直接复用思想 | 低 | 支撑可编辑架构/流程图 |
| `generating-mermaid-diagrams` | `forcedotcom/afv-library` | Mermaid 图生成 | 图示建模 | Mermaid | 参考实现 | 低 | 可补充图示 QA |
| `033-architecture-diagrams` | `jabrena/cursor-rules-java` | 架构图 | 系统组件和关系图 | Diagram rules | 参考实现 | 中 | 对系统论文很有用 |
| `diagram-generator` | `camoa/claude-skills` | 通用图生成 | 概念图、流程图 | Prompt workflow | 参考实现 | 中 | 可加入 Visual Planner 备选 |
| `arch-diagrams` | `alphaonedev/openclaw-graph` | 架构图 | 系统架构可视化 | Graph / diagram workflow | 参考实现 | 中 | 增强 Architecture Diagram |
| `architecture` | `markdown-viewer/skills` | 架构文档和图 | 架构解释、结构图 | Markdown / diagram | 参考实现 | 中 | 支撑 framework slides |
| `eraser-diagrams` | `eraserlabs/eraser-io` | 专业架构图 | Eraser diagram syntax、工程架构图 | Eraser DSL | 高，参考实现 | 中到高 | 可做高质量架构图候选后端 |
| `cloud` | `markdown-viewer/skills` | 云架构图 | cloud components | Markdown / diagram | 低优先级 | 中 | 仅特定论文有用 |
| `architecture-documentation` | `melodic-software/claude-code-plugins` | 架构文档 | 文档化、图示化 | Prompt workflow | 参考实现 | 中 | 可增强系统框架说明 |
| `architecture-diagram` | `mathews-tom/praxis-skills` | 架构图生成 | 系统组件、关系、布局 | Diagram workflow | 高，参考实现 | 中 | 适合 System Framework 页 |
| `aws-architecture-diagram` | `automateyournetwork/netclaw` | AWS 架构图 | 云服务图标和连接 | Cloud diagram | 不建议迁移 | 中 | 非通用学术场景 |
| `scientific-visualization` | `davila7/claude-code-templates` | 科学可视化 | 图表类型选择、数据表达 | Python / plotting | 高，参考实现 | 中 | 支撑 Results 重绘 |
| `generate-image` | `davila7/claude-code-templates` | 图像生成 | 图像 prompt / generation | Image workflow | 参考实现 | 中 | 可辅助概念页 |
| `scientific-skills` | `oimiragieo/agent-studio` | 科研技能集合 | scientific workflow | Skill suite | 参考实现 | 中 | 作为科研 pipeline 参考 |
| `scientific-visualization` | `jackspace/claudeskillz` | 科学图表 | 数据可视化 | plotting workflow | 高，参考实现 | 中 | 可提升实验结果页 |
| `diagram-skills` | `wentorai/research-plugins` | 研究图示 | diagram generation | Diagram plugins | 参考实现 | 中 | 可补充可视化后端 |

### 5.4 Slide Designer / Presentation / Review

| Skill Name | Repository | 解决的问题 | 核心能力 | 实现方式 | 是否适合迁移 | 迁移成本 | 预期收益 |
|---|---|---|---|---|---|---|---|
| `figma-use-slides` | `figma/mcp-server-guide` | Figma slides | Figma 设计和 slides | Figma MCP | 低优先级 | 高 | 设计能力强，但依赖复杂 |
| `slide deck designer` | `jmsktm/claude-settings` | slide deck 设计 | 版式、故事线 | Prompt workflow | 高，参考实现 | 中 | 增强 Presentation Designer |
| `canva-presentation-time-fitting` | `canva-sdks/canva-claude-skills` | 演讲时长适配 | slide count、讲稿时长 | Canva workflow | 参考实现 | 中到高 | 可用于 10/15/30 分钟模式 |
| `tufte-slide-design` | `ingpoc/skills` | Tufte 风格 slide | 信息密度、留白、图表优先 | Design rules | 高，参考实现 | 低到中 | 强化简洁学术版式 |
| `present` | `glebis/claude-skills` | 演讲支持 | presentation flow、talk prep | Prompt workflow | 参考实现 | 中 | 可补充 speaker notes |
| `giving-presentations` | `oldwinter/skills` | 演讲表达 | 演讲准备、表达建议 | Prompt workflow | 参考实现 | 低 | 增强讲稿和口头叙事 |
| `academic-presentations` | `boom5426/nature-paper-skills` | 学术演示 | 学术 PPT 结构、口头汇报 | Skill workflow | 高，参考实现 | 中 | 与目标高度一致 |
| `academic-pptx` | `gabberflast/academic-pptx-skill` | 学术 PPTX | PPTX 生成、学术风格 | PPTX workflow | 高，参考实现 | 中 | 可能补强 PPTX 输出 |
| `review-presentation` | `pamelafox/presentation-skills` | 评审演示文稿 | slide-by-slide review | Review workflow | 高，参考实现 | 低到中 | 直接支撑 Discriminator |
| `peer-review` | `davila7/claude-code-templates` | 同行评审 | 结构化反馈 | Review workflow | 参考实现 | 中 | 可借鉴评审维度 |
| `web-design-reviewer` | `github/awesome-copilot` | Web 设计评审 | 可读性、美观、UI QA | Review prompt | 参考实现 | 低 | 对 HTML presentation 视觉评审有用 |
| `multi-reviewer-patterns` | `wshobson/agents` | 多 reviewer 模式 | 多视角 review aggregation | Multi-agent pattern | 高，参考实现 | 中 | 支撑 Professor Panel |
| `critique` | `pbakaus/impeccable` | 批判性评审 | 设计/内容 critique | Critique workflow | 高，参考实现 | 中 | 可加入反思式优化 |
| `design-critique` | `anthropics/knowledge-work-plugins` | 设计批评 | 视觉设计、信息架构反馈 | Design critique | 高，参考实现 | 中 | 强化视觉审美 |
| `design-critique` | `owl-listener/designer-skills` | 设计评审 | layout、hierarchy、polish | Design workflow | 参考实现 | 中 | 支撑 Visual Quality 评分 |
| `critique` | `nexu-io/open-design` | 开放设计批评 | 视觉 QA、改进建议 | Design critique | 高，参考实现 | 中 | 可和 HTML/PPT 设计链结合 |
| `academic-paper-review` | `bytedance/deer-flow` | 学术论文评审 | novelty、soundness、clarity | Reviewer workflow | 高，参考实现 | 中 | 可迁移到科学性审查 |
| `icml-reviewer` | `sundial-org/skills` | ICML 风格 reviewer | 学术评审、打分 | Reviewer prompt | 高，参考实现 | 中 | 可形成领域无关 reviewer rubric |
| `paper-reviewer-simulator` | `a-green-hand-jack/ml-research-skills` | 模拟论文 reviewer | 强弱点、质疑点 | Reviewer simulator | 高，参考实现 | 中 | 支撑老教授/审稿人视角 |
| `paper-evidence-board` | `a-green-hand-jack/ml-research-skills` | 论文证据板 | claim-evidence mapping | Evidence board | 高，参考实现 | 中 | 避免 PPT 夸大论文结论 |
| `paper-review-skills` | `wentorai/research-plugins` | 论文评审 | 评审建议、问题定位 | Reviewer plugin | 参考实现 | 中 | 补充 reviewer pattern |

### 5.5 Academic Writing

| Skill Name | Repository | 解决的问题 | 核心能力 | 实现方式 | 是否适合迁移 | 迁移成本 | 预期收益 |
|---|---|---|---|---|---|---|---|
| `academic-writing` | `poemswe/co-researcher` | 学术写作 | 论文表达、结构化论证 | Writing workflow | 参考实现 | 中 | 可提升讲稿表达 |
| `academic-research-suite` | `imbad0202/academic-research-skills-codex` | 学术研究集合 | 搜索、写作、综述 | Skill suite | 参考实现 | 中 | 可借鉴研究 agent 组合 |
| `academic-research-skills-codex` | `aradotso/codex-skills` | 学术研究技能 | research / writing workflow | Skill suite | 参考实现 | 中 | 可借鉴结构 |
| `academic-writing-refiner` | `zihan-zhu/academic-writing-refiner` | 学术语言润色 | 精炼、清晰、正式表达 | Writing prompt | 低优先级 | 低 | 用于 notes / speaker script |

## 6. 迁移优先级总览

### 直接复用或轻量封装

1. `paper-to-group-meeting-ppt` 当前代码作为 baseline。
2. `mermaid-diagram` 的 diagram generation + syntax verification。
3. `slides-polish` 的 rendered-preview QA 思路。
4. `nature-reviewer` 的 groundedness / non-invention 规则。
5. `academic-plotting` 的 scientific chart 和 system diagram 思路。

### 重点参考实现

1. `ian-xiaohei-illustrations`
   - 迁移 concept visual brief，而不是迁移插画风格。
2. `yao-expert-skill`
   - 迁移专家评审、证据边界、结构化反馈、多轮优化。
3. `nature-paper2ppt`
   - 迁移 paper type routing、图表优先讲解、speaker notes。
4. `paper-reviewer-simulator` / `icml-reviewer` / `academic-paper-review`
   - 迁移科学性审查和审稿人质疑维度。
5. `html-presentation` / `html-presentation-beautifier` / `elegant-reports`
   - 迁移 HTML presentation 结构和视觉 polish 规则。
6. `tufte-slide-design` / `slide deck designer`
   - 迁移学术 slide 的视觉层级、留白和信息密度规则。

### 需要自行开发

1. Paper Understanding 到 Slide Story 的中间数据模型。
2. Visual-first slide architect：
   - 先定 page goal 和 visual subject，再定文字。
3. PDF figure extraction 的精确边界检测和质量评分。
4. HTML 与 PPTX 的统一 deck model。
5. Layout Validator：
   - text overflow
   - image clipping
   - object collision
   - chart readability
   - font readability
6. Iteration Controller：
   - Generator -> Visualizer -> Professor Reviewer -> Generator
   - 每轮保存修改原因和证据。

## 7. 初步结论

现有 skill 的下一步演进，不应该从“再找一个更好的 PDF 截图工具”开始，而应该从“建立 Academic Presentation Agent 的中间表示”开始。

原因是：截图不全、页面遮挡、文字太多、版式单一，本质上不是单个工具问题，而是缺少统一的 planning layer：

1. Paper Understanding 只知道论文里有什么。
2. Story Designer 决定听众应该按什么顺序理解。
3. Slide Architect 决定每页只承载什么。
4. Visual Planner 决定用图、流程、对比、表格还是重绘图表。
5. Renderer 才负责 HTML / PPTX。
6. Validator 和 Reviewer 负责闭环优化。

这意味着后续代码演进的核心不是“PDF -> PPT”，而是：

```text
Paper -> Evidence Model -> Storyboard -> Visual Plan -> Deck Model -> Rendered Outputs -> Review Loop
```

