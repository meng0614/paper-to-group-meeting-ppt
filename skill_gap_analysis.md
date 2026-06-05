# Skill Gap Analysis: From PDF-to-PPT Tool to Academic Presentation Agent

生成日期：2026-06-05

项目：`paper-to-group-meeting-ppt-release`

本文件分析当前 skill 与理想 Academic Presentation Agent 的差距。目标不是继续优化“论文摘要 PPT”，而是构建 Visual-first、Story-first、Audience-first 的学术汇报代理。

## 1. 理想系统定义

理想 Academic Presentation Agent 应完成以下链路：

```text
PDF / Code / Supplementary Materials
-> Paper Understanding
-> Evidence Ledger
-> Research Story Design
-> Slide Architect
-> Visual Planner
-> Figure / Diagram / Chart Generator
-> HTML / PPTX Renderer
-> Layout Validator
-> Professor Reviewer
-> Iterative Optimization
```

核心目标：

1. 帮助没读过论文的人在 10-15 分钟内理解论文最重要内容。
2. 每页只表达一个核心观点。
3. 每页先设计视觉主体，再决定文字。
4. 图表不是装饰，而是承载论证。
5. 评审机制同时检查科学准确性、叙事逻辑、视觉质量和可讲解性。

## 2. 当前项目能力基线

当前 `paper-to-group-meeting-ppt-release` 已经具备较好的初始基础：

1. PDF 解析和论文内容提取。
2. 基于论文生成 PPT / HTML 的基本流程。
3. Visual-first、Slide Architect、Layout Validator、Discriminator 等概念已经被引入。
4. 能生成 `review_report.md`、`improvement_history.md`、`layout_check_report.md`。
5. 已经支持 HTML report 和 PPTX 输出方向。
6. 已经开始关注图片截取边界、图像清晰度、布局重叠和页面容量。

但它仍然明显受到早期 `PDF -> PPT` 工具思维影响：

1. 内容生成仍偏 Text-first。
2. 图像处理仍偏“截论文图”，而不是“选择/简化/重绘视觉论据”。
3. 页面设计仍偏模板填充，缺少每页独立的视觉策略。
4. Reviewer 更多像质量检查器，还没有形成真正的教授式批判反馈。
5. 多轮优化机制尚未和中间表示深度绑定。

## 3. 十个能力维度差距分析

### 3.1 Paper Understanding

| 项目 | 当前状态 | 理想状态 | 差距等级 | 可迁移 Skill | 设计含义 |
|---|---|---|---|---|---|
| 论文结构识别 | 能提取标题、章节、图表、摘要式信息 | 自动识别论文类型、贡献链、方法链、证据链和局限性 | 中 | `nature-paper2ppt`, `agentic-paper-digest-skill`, `method-section-explainer` | 需要 `paper_model.json`，不只是文本摘要 |
| 事实边界 | 可总结论文内容，但事实/推断/简化边界不稳定 | 所有 slide claim 都能回溯到论文证据 | 高 | `yao-expert-skill`, `paper-evidence-board`, `nature-reviewer` | 需要 Evidence Ledger |
| 图表理解 | 能提取或截图图表，但常出现边界和语义不清 | 理解每张图回答的问题、变量、趋势、结论 | 高 | `academic-plotting`, `figure-description`, `scientific-visualization` | 需要 figure semantic parser |
| 局限性识别 | 可生成局限性页 | 能区分作者明确局限、实验不足、审稿人可能质疑 | 中 | `nature-reviewer`, `paper-reviewer-simulator` | 需要 Reviewer 与 Paper Understanding 联动 |

结论：当前最大问题不是“读不出摘要”，而是没有把论文内容转化为可验证的 evidence model。

### 3.2 Story Design

| 项目 | 当前状态 | 理想状态 | 差距等级 | 可迁移 Skill | 设计含义 |
|---|---|---|---|---|---|
| 故事线 | 基本按 Background / Method / Experiment / Results | 按 Problem -> Challenge -> Idea -> Method -> Result -> Takeaway 设计 | 高 | `paper-slides`, `giving-presentations`, `academic-presentations` | 需要 Story Designer Agent |
| 观众视角 | 有 Page Goal 概念 | 每页先回答“5 秒内观众记住什么” | 中 | `ian-xiaohei-illustrations`, `tufte-slide-design` | Page Goal 要进入 deck schema |
| 报告时长 | 尚未形成严格 10/15/30 分钟模式 | 自动根据时长调整 slide count 和内容深度 | 中 | `canva-presentation-time-fitting`, `paper-slides` | 需要 talk mode |
| 信息取舍 | 容易想覆盖论文全部内容 | 主动放弃细节，服务口头讲解 | 高 | `slides-polish`, `presentation review` skills | 需要 content budget |

结论：当前项目已经有“页面目标”，但还缺少真正的 story spine。每页应服务整场报告，而不是服务论文章节。

### 3.3 Visual Design

| 项目 | 当前状态 | 理想状态 | 差距等级 | 可迁移 Skill | 设计含义 |
|---|---|---|---|---|---|
| 视觉优先 | 已提出 Visual-first rule | 每页先确定视觉主体，视觉面积不少于 40% | 中 | `html-presentation-beautifier`, `tufte-slide-design`, `design-critique` | 需要 visual subject 强约束 |
| 视觉层级 | 有标题、图、文字，但权重有时混乱 | 标题 > 视觉主体 > 解释文字，留白参与设计 | 高 | `slide deck designer`, `slides-polish` | 需要 layout tokens |
| 版式多样性 | 页面容易模板化 | 根据 Page Goal 选择不同 layout archetype | 高 | `elegant-reports`, `html-presentation` | 需要 layout library |
| 风格学习 | 容易学习参考 PPT 的颜色和字体 | 学习设计哲学，不复制具体配色字体 | 中 | 用户给出的参考 PPT 分析规则 | 需要 style philosophy extractor |

结论：当前项目需要从“套模板”升级到“layout archetype selection”。

### 3.4 Concept Illustration

| 项目 | 当前状态 | 理想状态 | 差距等级 | 可迁移 Skill | 设计含义 |
|---|---|---|---|---|---|
| 抽象概念可视化 | 主要依赖论文原图和简单图示 | 能把抽象研究动机、冲突、挑战转成概念图 | 高 | `ian-xiaohei-illustrations`, `baoyu-diagram`, `diagram-generator` | 需要 Concept Visualizer |
| 视觉隐喻 | 尚未系统化 | 为每个抽象点生成 visual metaphor | 高 | `ian-xiaohei-illustrations` | 需要 visual brief schema |
| 学术风格 | 避免卡通化的机制还不明确 | 插图应专业、克制、解释性强 | 中 | `tufte-slide-design`, `design-critique` | 需要 academic illustration style guide |
| 生成质量审查 | 当前偏 layout check | 需要判断图示是否真的帮助理解 | 高 | `presentation review`, `yao-expert-skill` | Reviewer 要评价 visual meaning |

结论：最值得从 `ian-xiaohei-illustrations` 学的不是插画风格，而是“概念 -> 认知锚点 -> 画面构图 -> 视觉 QA”的流程。

### 3.5 Architecture Diagram

| 项目 | 当前状态 | 理想状态 | 差距等级 | 可迁移 Skill | 设计含义 |
|---|---|---|---|---|---|
| 方法框架图 | 多依赖论文原图截图 | 自动重构系统框架、模块关系、数据流 | 高 | `mermaid-diagram`, `academic-plotting`, `architecture-diagram`, `eraser-diagrams` | 需要 Architecture Diagram Agent |
| 可编辑性 | 截图不可编辑 | PPT 中用 shapes / connectors 或 SVG 生成 | 高 | `mermaid-diagram`, `html-ppt` | 图示应尽量可编辑 |
| 布局控制 | 复杂图容易挤 | 自动选择 pipeline / layered / network / matrix 布局 | 高 | `mermaid-diagram` best practices | 需要 diagram layout planner |
| 准确性 | 可能误画方法关系 | 图中每个模块关联 paper evidence | 高 | `paper-evidence-board`, `yao-expert-skill` | 图示也要证据绑定 |

结论：Architecture Diagram 是从摘要 PPT 走向学术报告的核心能力之一，不能只靠截图。

### 3.6 Scientific Visualization

| 项目 | 当前状态 | 理想状态 | 差距等级 | 可迁移 Skill | 设计含义 |
|---|---|---|---|---|---|
| 论文图复用 | 已尝试截图，但边界和清晰度问题明显 | 原图复用、简化重绘、重新绘制三种策略自动选择 | 高 | `academic-plotting`, `scientific-visualization`, `paper-plot` | 需要 figure strategy selector |
| 结果页表达 | 容易直接放论文图 | 每个结果图必须回答 So What | 高 | `tufte-slide-design`, `academic-plotting` | 需要 result claim extractor |
| 数据重绘 | 尚未系统化 | 能从文本/OCR/图表提取核心数据，重绘简化图 | 高 | `scientific-visualization` | 需要 chart redraw pipeline |
| 图像质量 | 已关注截图不全/模糊 | 自动检测清晰度、裁切、caption、轴标签可读性 | 高 | `slides-polish`, `layout validator` | 需要 figure quality scorer |

结论：实验页不应以“截图论文图”为默认策略。高水平报告往往会重绘或简化关键趋势图。

### 3.7 HTML Presentation

| 项目 | 当前状态 | 理想状态 | 差距等级 | 可迁移 Skill | 设计含义 |
|---|---|---|---|---|---|
| HTML 输出 | 已支持 HTML report | HTML 是第一类 presentation format，不只是辅助预览 | 中 | `html-presentation`, `elegant-reports`, `html-presentation-beautifier` | 需要 HTML deck model |
| Section 组织 | 已可按 section 输出 | Section 与 slide story 同源，支持滚动、折叠、动态图表 | 中 | `html-presentation` | 需要 section layout schema |
| PPTX 转换 | 已要求 HTML -> PPTX | HTML 和 PPTX 应从同一 deck model 渲染 | 高 | `html-ppt`, `slide-creator` | 需要 renderer abstraction |
| 可读性 | HTML 可读，但 presentation 感不稳定 | 像网页 slide deck，而不是长报告 | 中 | `elegant-reports` | 需要 page-by-page HTML layout |

结论：HTML 不应是“多一点文字的文档”，而应是 PPT 风格的可读 presentation 版本。

### 3.8 Layout Validation

| 项目 | 当前状态 | 理想状态 | 差距等级 | 可迁移 Skill | 设计含义 |
|---|---|---|---|---|---|
| 文字溢出 | 已能检查，但修复策略仍粗 | 优先拆页、换 layout、精简内容，最后才调字号 | 中 | `slides-polish`, `web-design-reviewer` | 需要 layout repair policy |
| 对象遮挡 | 已发现遮挡问题 | 自动检测 text/image/chart/object collision | 高 | browser screenshot QA, `slides-polish` | 需要 rendered layout validation |
| 图片裁切 | 已暴露明显问题 | 图像边界检测、caption 匹配、clip quality score | 高 | 自研 + PDF tools | 需要 figure extraction validator |
| 字体可读 | 已关注字体过小 | 结合 slide size、距离、目标时长给出阈值 | 中 | `presentation review` | 需要 readability thresholds |
| 页面过载 | 仍会塞内容 | 超容量自动拆页 | 高 | `Slide Architect` 自研 | 需要 capacity model |

结论：Layout Validator 不能只是“发现错”，还要能把错误反馈到 Slide Architect，而不是仅在渲染层缩小字体。

### 3.9 Professor Review

| 项目 | 当前状态 | 理想状态 | 差距等级 | 可迁移 Skill | 设计含义 |
|---|---|---|---|---|---|
| 评审角色 | 已有 Discriminator 概念 | 教授/领域专家/设计 reviewer 多角色并行 | 中 | `yao-expert-skill`, `nature-reviewer`, `multi-reviewer-patterns` | 需要 reviewer panel |
| 科学性 | 能输出建议 | 必须检查每个 slide claim 是否忠实论文 | 高 | `paper-evidence-board`, `academic-paper-review` | 需要 claim-evidence linking |
| 逻辑性 | 能评价故事线 | 判断是否形成 Problem -> Challenge -> Idea -> Result | 中 | `paper-slides`, `giving-presentations` | 需要 story score |
| 视觉性 | 能指出排版问题 | 判断视觉主体是否承载核心观点 | 高 | `design-critique`, `review-presentation` | 需要 visual meaning rubric |
| 可汇报性 | 有 presentation readiness | 需要 10/15/30 分钟口头讲解版本 | 中 | `canva-presentation-time-fitting` | 需要 speaker mode |

结论：Professor Reviewer 应从“挑错”升级为“约束生成器的专家反馈系统”。

### 3.10 Iterative Optimization

| 项目 | 当前状态 | 理想状态 | 差距等级 | 可迁移 Skill | 设计含义 |
|---|---|---|---|---|---|
| 优化循环 | 已有 Generator / Discriminator 概念 | 每轮修改由具体 reviewer evidence 驱动 | 中 | `yao-expert-skill`, `critique`, `multi-reviewer-patterns` | 需要 iteration state |
| 修改记录 | 已有 improvement history | 记录改动、原因、影响、未解决问题 | 中 | `slides-polish` versioning | 需要 history schema |
| 终止条件 | 已有评分阈值 | 结合科学性、布局通过、视觉质量和时间适配 | 中 | `review-presentation` | 需要 stopping criteria |
| 自动修复 | 目前更多是局部修补 | 能回退到 story/page/visual plan 层重规划 | 高 | 自研 | 需要 hierarchical repair |

结论：优化循环不能只在 PPT 渲染后微调。真正有效的循环应能回到 Paper Understanding、Story Design 和 Slide Architect 层。

## 4. 根因分析

当前问题表面上是：

1. 图截得不全或截多。
2. 图像不清晰。
3. 句子之间遮挡。
4. 框遮住文字。
5. 页面布局千篇一律。
6. 内容像论文摘要。

根因是：

1. 缺少统一中间表示。
   - 论文事实、故事线、视觉计划、页面对象、审查意见没有连接成同一套数据结构。
2. 缺少容量模型。
   - 生成内容时没有先判断页面能承载多少。
3. 缺少视觉策略选择。
   - 所有页面都接近“标题 + 图 + bullets”，没有根据 Page Goal 选择 layout。
4. 缺少图像语义理解。
   - PDF figure extraction 只做物理裁切，没有理解 caption、子图、上下文和图像质量。
5. 缺少教授式反馈的硬约束。
   - Reviewer 的意见没有强制回写到下一轮 generation schema。

## 5. 建议的核心架构

### 5.1 中间表示

后续应引入以下中间文件：

| 文件 | 作用 |
|---|---|
| `paper_model.json` | 论文事实模型：问题、方法、实验、贡献、局限、图表索引 |
| `evidence_ledger.json` | slide claim 到论文证据的映射 |
| `storyboard.json` | 报告故事线：Problem -> Challenge -> Idea -> Method -> Result -> Takeaway |
| `visual_plan.json` | 每页视觉主体、视觉类型、图表策略、5-second takeaway |
| `deck_model.json` | HTML / PPTX 共用页面模型 |
| `layout_report.json` | 自动布局检测结果 |
| `review_report.md` | Professor Reviewer 结构化评审 |
| `improvement_history.md` | 每轮修改记录 |

### 5.2 Agent 分工

```text
Paper Understanding Agent
  -> Evidence Ledger Builder
  -> Story Designer
  -> Slide Architect
  -> Visual Planner
  -> Concept Illustrator / Diagram Generator / Scientific Visualizer
  -> HTML Renderer / PPTX Renderer
  -> Layout Validator
  -> Professor Reviewer
  -> Iteration Controller
```

### 5.3 关键原则

1. One Slide One Message
   - 每页只表达一个核心观点。
2. Visual First
   - 每页先有视觉主体，再配文字。
3. Story First
   - 按听众理解路径组织，而不是按论文章节组织。
4. Evidence Bound
   - 每个 slide claim 都能回到论文证据。
5. Layout Before Rendering
   - 生成内容前先估算页面容量。
6. Repair at the Right Layer
   - 内容过载回到 Slide Architect。
   - 视觉不清回到 Visual Planner。
   - 事实不准回到 Paper Understanding。
   - 遮挡溢出回到 Renderer / Layout Validator。

## 6. 优先解决的差距

最高优先级差距：

1. 建立 `paper_model`、`storyboard`、`visual_plan`、`deck_model` 四层数据模型。
2. 改造生成逻辑为：
   ```text
   Page Goal -> Visual Subject -> Content -> Layout
   ```
3. 重构图像策略：
   ```text
   原图复用 -> 原图裁切验证 -> 子图识别 -> 简化重绘 -> 概念图替代
   ```
4. 引入真正的 Professor Reviewer：
   - 科学性
   - 故事线
   - 视觉层级
   - 可汇报性
   - 听众视角
5. 让优化循环能回到 planning 层，而不是只修 PPT 对象。

## 7. 验证标准

后续 skill 更新完成后，可用用户提供的 PDF：

`C:\Users\30430\Zotero\storage\8T2TWGCI\Falk 等。 - 2020 - Time-Triggered Traffic Planning for Data Networks .pdf`

作为验证样例。验证时不应只检查是否生成 PPT，而应检查：

1. 是否形成面向听众的故事线。
2. 是否每页有明确 Page Goal。
3. 是否每页有视觉主体，且视觉面积足够。
4. 是否避免文字摘要化。
5. 是否存在截图边界错误。
6. 是否存在文字/图/框遮挡。
7. 是否生成 HTML 和可编辑 PPTX。
8. 是否生成 reviewer report 和 improvement history。
9. 是否能解释每轮优化为什么发生。
10. 是否适合 10-15 分钟组会汇报。

