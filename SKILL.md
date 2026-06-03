---
name: paper-to-group-meeting-ppt
description: Generate a visual-first academic group-meeting HTML report and editable PPTX deck from one or more research paper PDFs. Use when the user asks to turn arbitrary literature PDFs into a paper-reading report, group meeting presentation, literature sharing HTML, journal club explanation, editable PowerPoint, or wants paper understanding plus cropped figures/tables/algorithms, HTML/PPTX output, layout validation, expert review, and speaker notes.
---

# Paper to Group Meeting Presentation Agent

Create a general Academic Presentation Agent for arbitrary research papers. Do not assume a specific field such as TSN, networking, AI, medicine, biology, or systems.

The skill's core promise is:

```text
paper understanding -> visual storyboard -> section architect -> visualizer -> HTML report + editable PPTX -> layout/figure validators -> professor review -> refined outputs
```

The output should be a usable HTML report for a human presenter, not merely a paper summary.

The default strategy is **Presentation-first / Visual-first**, not Text-first. Before creating every section, write:

```text
Page Goal:
What should the audience understand if they see this slide for only 5 seconds?

Visual:
What visual form best conveys that goal? Use a scenario diagram, comparison, bottleneck sketch, framework, pipeline, flowchart, simplified chart, or key paper figure.

Content:
What minimal text is needed to support that visual?
```

Only after these three fields are clear should the section be rendered.

## Section Architect

Before rendering, run a Section Architect step. Its job is to decide:

- how many sections are needed;
- how much content each section can carry;
- which HTML layout each section should use.

Rule: prefer adding slides over shrinking fonts. Never solve content overload by making the page dense.

Use:

```powershell
python scripts/slide_architect.py --spec paper_ppt_project/intermediate/slide_specs.json --out paper_ppt_project/intermediate/slide_specs.architected.json --report paper_ppt_project/intermediate/slide_architect_report.md
```

The architect may split overloaded sections, for example:

- Method -> Method Overview / Method Details / Method Example
- Experiment -> Experimental Setup / Experimental Results / Experimental Analysis
- Result -> Main Result / Result Analysis / So What

For higher quality, support a Generator/Discriminator adversarial refinement loop:

```text
Generator -> Reviewer/Judge -> Revision Plan -> Generator
```

The Discriminator should act like a strict senior professor with 20+ years of research experience and critique scientific accuracy, storytelling, visual quality, audience readability, group-meeting suitability, and speaker notes.

## Prefer Existing Skills When Available

Use existing skills as sub-capabilities instead of reimplementing everything:

- `nature-reader`, `research-lit`, `comm-lit-review`, or similar: paper reading and research-problem extraction.
- `baoyu-slide-deck` or presentation-design skills: visual style, slide density, and final design polish when image-based slide generation is desired.
- domain-specific skills such as `tsn-paper-to-presentation`: domain vocabulary and stronger interpretation for specialized papers.

This skill coordinates the full workflow and supplies reusable scripts for PDF rendering, local figure/table/algorithm cropping, and PPTX/HTML generation.

## Output Layout

Create one output directory per run:

```text
paper_ppt_project/
  source/
    paper.pdf
  pages/
    page-01.png
  figures/
    fig_01_framework.png
    alg_01_main.png
    table_01_setup.png
  intermediate/
    paper_analysis.md
    figures_index.md
    slide_outline.md
    visual_storyboard.md
    slide_specs.json
    source_map.md
  final_presentation_generated.html
  final_presentation.html
  final_presentation_generated.pptx
  final_presentation.pptx
  layout_check_report.md
  figure_quality_report.md
  speaker_notes.md
  runs/                    # optional iterative refinement rounds
  final/                   # best refined deck
  improvement_history.md
```

## Workflow

Read `references/academic_presentation_agent.md` when the user asks for an optimized, iterative, professor-reviewed, or high-quality deck.

If the user provides a beautiful reference PPT, treat it as a style guide. Extract its dominant colors and fonts before rendering:

```powershell
python scripts/extract_reference_style.py --reference reference.pptx --out paper_ppt_project/intermediate/reference_style.json
```

Then copy the JSON object into `intermediate/slide_specs.json` under the top-level `style` key. The bundled renderer uses this style for the deck theme, title bar, accent line, font family, colors, and HTML preview.

### 1. Paper Understanding

Read the paper before designing slides. Produce `intermediate/paper_analysis.md` with:

- title, authors, year, venue if available;
- research background and problem;
- existing gap or motivation;
- core idea and method;
- model, assumptions, and key equations when important;
- algorithm steps and inputs/outputs;
- experimental setup: datasets/topologies/tools/baselines/metrics;
- main results and numbers;
- limitations and discussion questions.

Do not invent results. Mark uncertain items as `needs verification`.

### 2. Evidence Extraction

Find visual evidence that helps a presenter explain the paper:

- figures: framework, pipeline, system architecture, model diagrams, experiment topology;
- tables: settings, baselines, datasets, ablation results;
- algorithms: pseudocode blocks;
- result plots: curves, bars, CDFs, heatmaps.

Use `scripts/render_pdf_pages.py` to render PDF pages into PNGs if page images do not exist. Use at least 220 DPI for PPT-readable figures.

Default figure extraction order:

1. caption-aware crop with `scripts/crop_pdf_figures_by_caption.py`;
2. manually confirmed clean crop box with `scripts/crop_pdf_regions.py`;
3. connected-component expansion only as a single-figure fallback.

Create `intermediate/figures_index.md`:

```markdown
## Fig. 1 System Framework
- Type: framework
- Source page: 3
- Crop file: figures/fig_01_framework.png
- Used slides: 5
- Why it matters: shows the proposed workflow and component roles.
- How to explain: start from input, then control flow, then output.
```

Only crop figures/tables/algorithms that are useful for the talk. Avoid full-page screenshots unless the user explicitly requests them. Prefer caption-aware cropping:

```powershell
python scripts/crop_pdf_figures_by_caption.py --pdf paper_ppt_project/source/paper.pdf --pages paper_ppt_project/pages --spec caption_crop_specs.json --out paper_ppt_project/figures
```

Use manual clean boxes when caption-aware cropping is not enough, then validate quality:

```powershell
python scripts/crop_pdf_regions.py --pages paper_ppt_project/pages --spec crop_specs.json --out paper_ppt_project/figures --padding 24 --trim --min-width 1000
python scripts/figure_quality_validator.py --figures paper_ppt_project/figures --report paper_ppt_project/figure_quality_report.md
```

If `figure_quality_report.md` flags `possible_incomplete_crop`, re-crop with a larger clean box or caption-aware crop. If it flags `low_resolution`, re-render pages at a higher DPI before cropping.

For complex framework figures, connected-component repair may help, but use it only for one specific figure after visual inspection:

```powershell
python scripts/crop_pdf_regions.py --pages paper_ppt_project/pages --spec crop_specs.json --out paper_ppt_project/figures --component-expand --search-pad 320 --min-width 1000
```

If component repair includes page headers or body text, discard that crop and replace it with caption-aware or manually confirmed clean crop. The final PPT must not use a known incomplete or text-contaminated framework, algorithm, or experiment figure.

### 3. Slide Planning

Generate `intermediate/slide_outline.md` first, then generate `intermediate/visual_storyboard.md`.

For each page in `visual_storyboard.md`, include:

```markdown
## Slide N
- Page Goal:
- Visual:
- Content:
```

Default academic structure:

1. Title
2. Research Background
3. Problem Statement
4. Motivation
5. Challenges
6. Key Idea
7. System Framework / Pipeline
8. Method Details
9. Experimental Setup
10. Experimental Results
11. Discussion
12. Limitations
13. Future Work
14. Takeaways

For multiple papers, use: per-paper brief reading -> comparison matrix -> shared takeaways.

Then create `intermediate/slide_specs.json` for deterministic HTML rendering. Use `references/slide_spec_schema.md`.

When the user wants a compact 10-slide group-meeting structure, use:

```powershell
python scripts/create_10_slide_spec_template.py --project paper_ppt_project --lang zh
```

This creates a starter `intermediate/slide_specs.json` with:

1. title/authors/affiliations;
2. background and motivation;
3. core research problem;
4. existing method limitations;
5. proposed method overview;
6. core algorithm/mechanism;
7. experimental design;
8. experimental results;
9. contributions;
10. limitations and future work.

When the user wants a high-level talk rather than a literature-summary deck, prefer:

```powershell
python scripts/create_visual_first_spec_template.py --project paper_ppt_project --lang zh
```

Then replace the placeholders with paper-specific Page Goal, Visual, and Content entries.

### 4. Report and PPT Design

Use restrained academic HTML design. Respect `style` in `slide_specs.json` when present.

Visual-first rules:

- Background sections must not be text-only. Use a scenario, system, industry, statistics, or typical-case visual.
- Problem sections should show conflict: existing method vs paper setting, bottleneck, mismatch, or constraint collision.
- Method sections should use framework, pipeline, workflow, or architecture diagrams so the audience understands the method quickly.
- Algorithm sections should not directly paste pseudocode as the only content. Prefer flowcharts, decision flows, state transitions, or module relations; pseudocode can be embedded in a scrollable block.
- Experiment sections should explain the validation logic: setup -> baselines -> metrics -> claim.
- Result sections should redraw or simplify charts when possible: keep the trend, remove irrelevant curves, mark best results, and annotate key improvement.
- Every result visual must answer "So What?".
- Takeaways must explicitly state maximum contribution, maximum novelty, and maximum limitation.

- primary color default `#0E2557`;
- secondary color default `#4B649F`;
- accent color default `#FF0000`;
- neutral color default `#6B7280`;
- light background default `#F4F7FB`;
- title font default `Microsoft YaHei`;
- body font default `Microsoft YaHei`;
- title size 28-36 pt;
- body size 18-24 pt;
- assertion headlines;
- 16:9 layout;
- white or very light gray content slides;
- dark chapter divider only when useful;
- 2-5 bullets per slide;
- cropped paper figure should normally occupy 45-70% of the slide;
- algorithm slides: keep pseudocode large and readable;
- result slides: enlarge plots first, then add interpretation text;
- do not over-decorate.

Each slide should keep one visual center. Avoid text walls, multi-figure collage, and complex tables.

If `baoyu-slide-deck` or another mature design skill is available and the user wants highly polished visual slides, use it after generating the slide outline and evidence files.

### 5. HTML and Editable PPTX Rendering

Use:

```powershell
python scripts/build_html_report_from_spec.py --spec intermediate/slide_specs.json --out paper_ppt_project
```

The script generates:

- `final_presentation_generated.html`
- `final_presentation.html`
- `speaker_notes.md`

The HTML supports:

- multiple sections: Background / Problem / Method / Experiment / Results / Conclusion;
- at least one visual center per section;
- MathJax formulas;
- pseudocode blocks;
- foldable long text;
- scrollable tables;
- dynamic result bars.

Also generate an editable PowerPoint deck:

```powershell
python scripts/build_editable_pptx_from_spec.py --spec intermediate/slide_specs.json --out paper_ppt_project
```

The PPTX must be editable by the user:

- slide titles, Page Goal boxes, bullets, callouts, flow steps, comparison boxes, and result bars are PowerPoint text/shape objects;
- paper figures are inserted as replaceable image objects, not baked into a full-slide screenshot;
- layouts should vary across sections: figure-first, visual-left, visual-right, top-visual, comparison, flow, and result-focus;
- never convert the whole HTML page into a PPT image unless the user explicitly asks for a static screenshot deck.

### 6. Speaker Notes

Each section should have notes. Notes should not simply repeat visible text. Include:

- the core message of the slide;
- what part of the figure/table/algorithm to point at;
- transition from previous slide;
- one likely question or caveat when useful;
- source provenance.

### 7. Optional Generator/Discriminator Refinement Loop

When the user asks for iterative improvement, professor-style review, adversarial review, or a more polished final report, run a generator-reviewer loop.

Read these references when deeper guidance is needed:

- `references/generator_discriminator_loop.md`
- `references/academic_presentation_agent.md`
- `references/refinement_loop.md`
- `references/reviewer_rubric.md`
- `references/figure_extraction_backends.md`

Use:

```powershell
python scripts/refine_presentation_loop.py --project paper_ppt_project --rounds 3 --target-score 8.5
```

The loop creates:

- `runs/round_01/`, `runs/round_02/`, ...
- `slide_architect_report.md`
- `layout_check_report.md`
- `figure_quality_report.md`
- `reviewer_report.json`
- `reviewer_report.md`
- `revision_plan.md`
- `final/final_presentation_generated.html`
- `final/final_presentation.html`
- `final/final_presentation_generated.pptx`
- `final/final_presentation.pptx`
- `final/speaker_notes.md`
- `improvement_history.md`

The bundled script provides deterministic structural review, Slide Architect planning, Layout Validator checks, and automatic cleanup revisions. For true expert review, act as the reviewer yourself: inspect `paper_analysis.md`, `figures_index.md`, `slide_specs.json`, `slide_architect_report.md`, `layout_check_report.md`, and `final_presentation.html`; then write sharper revision tasks before the next generator pass.

Run 3-5 rounds by default. Stop earlier if all key scores reach 9/10, if the user is satisfied, or if the score no longer improves.

## Quality Gates

Before final response, verify:

- `final_presentation_generated.html` exists and is non-empty;
- `final_presentation_generated.pptx` exists, opens as a valid PPTX, and uses editable text/shape/image objects;
- `layout_check_report.md` exists and all required layout checks pass;
- `figure_quality_report.md` exists; any `NEEDS_REVIEW` figure is either re-cropped or explicitly documented;
- `slide_architect_report.md` exists and confirms overloaded sections were split or compacted;
- no full-page PDF screenshots are used unless requested;
- all cropped visuals have source paper/page in `figures_index.md`;
- section text is not a wall of text; long text is folded or scrollable;
- speaker notes exist for major sections;
- if refinement was requested, `reviewer_report.md`, `revision_plan.md`, and `improvement_history.md` exist;
- final response includes absolute paths to PPTX, HTML, and notes.

## Failure Handling

- If PDF text extraction is poor, render pages and use visual/caption-based analysis; tell the user OCR may be needed.
- If figure auto-cropping is unreliable, crop manually from rendered pages and document it.
- If no PPTX library exists, use the bundled OOXML renderer script.
- If the paper is very long or multi-paper input is large, first create a 12-15 slide version and save deeper notes separately.
