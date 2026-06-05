# Skill Evolution Roadmap: Academic Presentation Agent

生成日期：2026-06-05

项目：`paper-to-group-meeting-ppt-release`

目标：从 `PDF -> PPT` 工具升级为通用 Academic Presentation Agent。

本 roadmap 按 P0-P3 排序。每个阶段明确：

1. 需要实现的能力。
2. 哪些能力直接复用。
3. 哪些能力参考实现。
4. 哪些能力需要自行开发。
5. 验收标准。

## 1. 总体演进方向

### 1.1 旧定位

```text
PDF
-> 提取文字和图片
-> 填入 PPT 模板
-> 输出 PPTX
```

这个定位容易导致：

1. 内容像摘要。
2. 图像像截图。
3. 页面像模板填充。
4. 优化像排版修补。

### 1.2 新定位

```text
PDF / Supplementary Materials
-> Paper Understanding
-> Evidence Ledger
-> Story Design
-> Visual Design
-> Deck Generation
-> Professor Review
-> Iterative Optimization
-> HTML + PPTX + Reports
```

核心目标不是覆盖论文全部内容，而是让听众快速理解论文最重要的研究逻辑：

```text
Problem
-> Challenge
-> Key Idea
-> Method
-> Result
-> Takeaway
```

## 2. P0: Architecture Foundation

时间定位：立即开始，作为下一轮代码修改的第一批任务。

### 2.1 目标

先建立 Academic Presentation Agent 的骨架，避免继续在 PPT 渲染层修修补补。

P0 不追求生成最漂亮的 PPT，而是让系统具备正确的数据流：

```text
Paper Model
-> Storyboard
-> Visual Plan
-> Deck Model
-> Renderers
-> Validators
-> Review Loop
```

### 2.2 必做能力

| 能力 | 说明 | 来源策略 |
|---|---|---|
| `paper_model.json` | 保存论文问题、方法、实验、贡献、局限、图表索引 | 自行开发 |
| `evidence_ledger.json` | 保存 slide claim 与论文证据的映射 | 参考 `yao-expert-skill`, `paper-evidence-board`, `nature-reviewer` |
| `storyboard.json` | 保存报告故事线，不再直接按论文章节生成 | 参考 `paper-slides`, `nature-paper2ppt` |
| `visual_plan.json` | 每页保存 Page Goal、Visual Subject、Visual Type、5-second Takeaway | 参考 `ian-xiaohei-illustrations` |
| `deck_model.json` | HTML 和 PPTX 共用页面对象模型 | 自行开发 |
| `layout_check_report.md` | 输出布局检查结果 | 复用当前项目并增强 |
| `review_report.md` | Professor Reviewer 结构化反馈 | 参考 `yao-expert-skill`, `nature-reviewer` |
| `improvement_history.md` | 每轮修改原因与结果 | 复用当前项目并增强 |

### 2.3 直接复用

1. 当前 `paper-to-group-meeting-ppt-release` 的脚本结构。
2. 当前 HTML / PPTX 输出框架。
3. 当前 Generator / Discriminator / Layout Validator 的概念。
4. 当前 report 输出文件命名。

### 2.4 参考实现

1. `yao-expert-skill`
   - 事实、推断、假设、未知的边界声明。
   - 结构化专家反馈。
2. `ian-xiaohei-illustrations`
   - 抽象概念到 visual brief 的过程。
3. `nature-paper2ppt`
   - paper type routing。
   - 图表优先讲解。
4. `paper-slides`
   - talk type 和时长约束。

### 2.5 需要自行开发

1. 统一 deck schema。
2. 页面容量估计。
3. slide claim 与 evidence ledger 的绑定。
4. 从 reviewer feedback 回写到 storyboard / visual plan / deck model 的机制。

### 2.6 P0 验收标准

1. 每次生成都产生：
   - `paper_model.json`
   - `storyboard.json`
   - `visual_plan.json`
   - `deck_model.json`
   - `layout_check_report.md`
   - `review_report.md`
   - `improvement_history.md`
2. 每页都包含：
   - Page Goal
   - Visual
   - Content
   - 5-second Takeaway
3. 系统可以解释：
   - 为什么需要这一页。
   - 为什么选择这种视觉表达。
   - 哪些内容来自论文证据。

## 3. P1: Paper Understanding + Story Designer

时间定位：P0 完成后优先实现。

### 3.1 目标

让系统真正理解论文，而不是只生成摘要。

### 3.2 必做能力

| 能力 | 说明 | 来源策略 |
|---|---|---|
| Paper Type Router | 判断论文属于系统、算法、理论、实验、应用、综述等类型 | 参考 `nature-paper2ppt` |
| Contribution Chain Extractor | 提取问题、挑战、想法、方法、结果、贡献之间的链条 | 自行开发 |
| Method Decomposer | 把方法拆成模块、流程、关键机制 | 参考 `method-section-explainer` |
| Experiment Interpreter | 提取实验目标、设置、baseline、指标、结果趋势 | 参考 `academic-plotting`, `scientific-visualization` |
| Limitation Classifier | 区分作者局限、实验局限、审稿人可能质疑 | 参考 `nature-reviewer`, `paper-reviewer-simulator` |
| Audience Primer | 为非本领域听众生成必要背景 | 参考 `yao-expert-skill`, `getcompanion-ai/feynman/literature-review` |

### 3.3 直接复用

1. 当前 PDF 文字提取流程。
2. 当前图表索引和 caption 提取流程。

### 3.4 参考实现

1. `nature-paper2ppt`
   - 先判断论文类型，再决定 PPT 结构。
2. `method-section-explainer`
   - 将方法拆解为可讲解的机制单元。
3. `paper-evidence-board`
   - 建立 claim-evidence board。
4. `nature-reviewer`
   - 不臆造、不夸大、标注不可评估内容。

### 3.5 需要自行开发

1. `story_score`：
   - 是否形成完整故事线。
2. `audience_gap`：
   - 没读过论文的人会在哪些地方听不懂。
3. `slide_intent`：
   - 每页属于 Problem / Challenge / Idea / Method / Result / Takeaway 中哪一类。

### 3.6 P1 验收标准

1. 生成的 storyboard 不再机械复制论文结构。
2. 每页能回答一个问题：
   - 为什么做？
   - 哪里难？
   - 核心想法是什么？
   - 方法如何工作？
   - 实验证明了什么？
   - 局限是什么？
3. Professor Reviewer 能指出：
   - 哪些 slide claim 没有证据。
   - 哪些实验结论被过度简化或夸大。
   - 哪些背景对听众仍不够清楚。

## 4. P2: Visual-first Generation Engine

时间定位：P1 后进入重点建设。

### 4.1 目标

让输出从 Text-first 转为 Visual-first。每页先设计视觉主体，再安排文字。

### 4.2 必做能力

| 能力 | 说明 | 来源策略 |
|---|---|---|
| Concept Visualizer | 将抽象概念、冲突、挑战转成概念图 | 参考 `ian-xiaohei-illustrations`, `baoyu-diagram` |
| Architecture Diagram Agent | 将方法框架、系统组件、数据流转成可编辑图 | 直接/参考 `mermaid-diagram`, `architecture-diagram`, `eraser-diagrams` |
| Scientific Visualizer | 将结果趋势重绘为简洁图表 | 参考 `academic-plotting`, `scientific-visualization` |
| Figure Strategy Selector | 在原图复用、原图简化、重绘之间选择 | 自行开发 |
| Figure Boundary Validator | 检查图是否截全、截多、模糊、caption 错配 | 自行开发 |
| Layout Archetype Library | 为不同页面目标选择布局 | 参考 `tufte-slide-design`, `slide deck designer`, `elegant-reports` |

### 4.3 直接复用

1. `mermaid-diagram`
   - 流程图、架构图、时序图、状态图生成和语法验证。
2. 当前项目已有 HTML / PPTX 渲染基础。

### 4.4 参考实现

1. `ian-xiaohei-illustrations`
   - visual brief。
   - cognitive anchor。
   - concept-to-image prompt。
2. `academic-plotting`
   - 学术图表重绘。
   - 系统组件关系抽取。
3. `slides-polish`
   - 渲染后逐页视觉检查。
4. `design-critique`
   - 视觉层级、留白、布局审查。

### 4.5 需要自行开发

1. `visual_plan` schema：
   ```json
   {
     "slide_id": 3,
     "page_goal": "...",
     "visual_subject": "...",
     "visual_type": "comparison_diagram",
     "visual_strategy": "redraw",
     "source_evidence": ["Fig. 2", "Section III-B"],
     "five_second_takeaway": "..."
   }
   ```
2. PDF figure extraction 的精确边界算法。
3. 子图识别：
   - Fig. 4(a)
   - Fig. 4(b)
   - 复合图分块
4. 图像质量评分：
   - 清晰度
   - 边界完整度
   - caption 匹配
   - 轴标签可读性
5. HTML/PPTX 双渲染一致性。

### 4.6 P2 验收标准

1. 背景页不再只有文字，必须有场景/结构/冲突图。
2. 方法页不再是长 bullets，必须有 framework / pipeline / workflow。
3. 算法页不直接贴伪代码，而用流程图或决策图解释。
4. 实验结果页尽量重绘或简化图表，并明确 So What。
5. 每页视觉主体面积原则上不少于 40%。
6. 不同页面有不同 layout archetype，避免千篇一律。

## 5. P3: Professor Review + Autonomous Optimization

时间定位：P2 后完善，形成可发布版本。

### 5.1 目标

构建真正的 Generator + Professor Reviewer + Visual Reviewer + Layout Validator 闭环。

### 5.2 必做能力

| 能力 | 说明 | 来源策略 |
|---|---|---|
| Professor Reviewer Panel | 多视角评审：科学性、故事线、视觉、可汇报性 | 参考 `yao-expert-skill`, `nature-reviewer`, `multi-reviewer-patterns` |
| Design Critic | 专门评价视觉层级、布局、留白、图表清晰度 | 参考 `design-critique`, `review-presentation` |
| Evidence Auditor | 检查每个 slide claim 是否有论文证据 | 参考 `paper-evidence-board`, `academic-paper-review` |
| Iteration Controller | 决定下一轮修 story、修 visual、修 layout 还是修 evidence | 自行开发 |
| Benchmark Suite | 用多学科论文验证通用性 | 自行开发 |
| Release QA | 输出 README、示例、测试 PDF、demo outputs | 自行开发 |

### 5.3 直接复用

1. 当前 `review_report.md` 和 `improvement_history.md` 文件输出。
2. 当前 `layout_check_report.md` 思路。

### 5.4 参考实现

1. `yao-expert-skill`
   - 专家式结构化反馈。
2. `nature-reviewer`
   - 事实基座和非臆造。
3. `review-presentation`
   - slide-by-slide presentation review。
4. `multi-reviewer-patterns`
   - 多 reviewer 聚合。
5. `slides-polish`
   - 渲染图像后的视觉检查和版本化。

### 5.5 需要自行开发

1. Review feedback 到 deck model 的结构化 patch。
2. 多轮优化状态机：
   ```text
   draft
   -> layout_checked
   -> professor_reviewed
   -> revision_planned
   -> regenerated
   -> final_checked
   ```
3. 停止条件：
   - Scientific Accuracy >= 9
   - Storytelling >= 9
   - Visual Quality >= 9
   - Presentation Readiness >= 9
   - Layout Validator pass
4. 自动回退层级：
   - 内容事实错：回到 Paper Understanding。
   - 故事线弱：回到 Story Designer。
   - 图示表达弱：回到 Visual Planner。
   - 排版错误：回到 Renderer / Layout Validator。

### 5.6 P3 验收标准

1. 每轮优化都有明确修改原因。
2. Reviewer 不能只给泛泛建议，必须逐页 KEEP / REMOVE / ADD / MODIFY。
3. 系统能自动判断应在哪个层级修复问题。
4. 最终输出包含：
   - `final_presentation_generated.html`
   - `final_presentation_generated.pptx`
   - `review_report.md`
   - `layout_check_report.md`
   - `improvement_history.md`
5. 输出内容适合 10-15 分钟组会汇报。

## 6. 推荐实施顺序

### Step 1: 固化数据模型

先新增数据模型，不急于改变所有渲染细节。

优先实现：

1. `paper_model.json`
2. `storyboard.json`
3. `visual_plan.json`
4. `deck_model.json`

### Step 2: 改写生成入口

把生成流程从：

```text
extract paper text -> generate slides
```

改成：

```text
extract paper facts
-> build story
-> plan visuals
-> build deck model
-> render HTML/PPTX
```

### Step 3: 优先修复图像问题

用户当前最明显痛点是：

1. 图截不全。
2. 图截太多。
3. 图不清楚。

因此 P2 中的 Figure Strategy Selector 和 Figure Boundary Validator 应前置实现一版轻量方案。

轻量策略：

1. caption 定位。
2. 图像区域候选框检测。
3. caption 与图像距离约束。
4. 留白边界检测。
5. OCR / text density 过滤正文区域。
6. 导出图像后做清晰度和边缘检查。

### Step 4: 再做视觉多样化

页面布局至少应支持：

1. Hero takeaway。
2. Problem comparison。
3. Before / After。
4. Pipeline。
5. Layered architecture。
6. Algorithm flow。
7. Experiment matrix。
8. Result chart with So What annotation。
9. Limitation / future work split。
10. Final takeaways。

### Step 5: 建立自动评审闭环

最后再把 Professor Reviewer 深度接入优化循环。

## 7. 外部 Skill 迁移策略

### 7.1 直接复用

| 能力 | Skill |
|---|---|
| Mermaid 图生成和验证 | `mermaid-diagram` |
| 已生成 slides 视觉审查思路 | `slides-polish` |
| Nature-style grounded review | `nature-reviewer` |
| 当前 PDF/HTML/PPTX 基线 | `paper-to-group-meeting-ppt-release` |

### 7.2 参考实现

| 能力 | Skill |
|---|---|
| 抽象概念可视化 | `ian-xiaohei-illustrations` |
| 专家评审机制 | `yao-expert-skill` |
| 论文类型路由 | `nature-paper2ppt` |
| 学术演讲结构 | `paper-slides`, `academic-presentations` |
| HTML presentation 美化 | `html-presentation`, `elegant-reports`, `html-presentation-beautifier` |
| 科学图表重绘 | `academic-plotting`, `scientific-visualization` |
| 设计批评 | `design-critique`, `review-presentation`, `critique` |

### 7.3 自行开发

| 能力 | 原因 |
|---|---|
| 统一 deck model | 这是本项目的核心 glue layer，外部 skill 很难直接满足 |
| figure boundary validator | 用户已反复指出具体问题，必须针对论文 PDF 场景自研 |
| page capacity model | 需要和 PPTX/HTML 渲染尺寸绑定 |
| hierarchical repair loop | 需要打通 planning、visual、render、review 四层 |
| claim-evidence ledger | 需要和本项目 PDF parser、slide generator 绑定 |

## 8. 用 Falk 论文验证的设计

用户提供的验证 PDF：

`C:\Users\30430\Zotero\storage\8T2TWGCI\Falk 等。 - 2020 - Time-Triggered Traffic Planning for Data Networks .pdf`

后续 skill 更新完成后，应使用该 PDF 进行验证。建议验证流程如下：

1. 运行 Academic Presentation Agent。
2. 检查是否生成 HTML 和 PPTX。
3. 检查 `paper_model.json` 是否正确识别：
   - 研究问题
   - time-triggered traffic planning 背景
   - 方法核心
   - 实验/评估
   - 局限性
4. 检查 `storyboard.json` 是否按报告故事线组织，而不是按论文章节复制。
5. 检查 `visual_plan.json`：
   - 每页是否有 Page Goal。
   - 每页是否有视觉主体。
   - 视觉策略是否合理。
6. 检查 PPTX：
   - 是否有截图边界错误。
   - 是否有图像模糊。
   - 是否有文字遮挡。
   - 是否有对象碰撞。
   - 是否可编辑。
7. 检查 review report：
   - 是否提出逐页 KEEP / REMOVE / ADD / MODIFY。
   - 是否指出科学性和故事线问题。
8. 检查 improvement history：
   - 是否记录每轮修改原因。

## 9. 最终判断

当前项目已经具备成为 Academic Presentation Agent 的基础，但需要一次架构层升级。

最重要的不是再加一个 PPT 模板，而是建立：

```text
Paper Understanding
-> Story Design
-> Visual Plan
-> Deck Model
-> Review Loop
```

只有这条链路建立起来，后续接入更好的截图工具、图表重绘工具、HTML/PPTX 渲染工具才有意义。

