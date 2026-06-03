---
name: paper-to-group-meeting-ppt
description: Generate a simple academic group-meeting presentation from one or more research paper PDFs. Use when the user asks to turn arbitrary literature PDFs into a paper-reading PPT, group meeting slides, literature sharing deck, journal club presentation, or wants paper understanding plus cropped figures/tables/algorithms, PPTX/HTML output, and speaker notes.
---

# Paper to Group Meeting PPT

Create a general Academic Presentation Agent for arbitrary research papers. Do not assume a specific field such as TSN, networking, AI, medicine, biology, or systems.

The skill's core promise is:

```text
paper understanding -> visual evidence optimization -> academic slide design -> professor review -> refined presentation
```

The output should be a usable first draft for a human presenter, not merely a paper summary.

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
    slide_specs.json
    source_map.md
  final_presentation.pptx
  final_presentation.html
  speaker_notes.md
  runs/                    # optional iterative refinement rounds
  final/                   # best refined deck
  improvement_history.md
```

## Workflow

Read `references/academic_presentation_agent.md` when the user asks for an optimized, iterative, professor-reviewed, or high-quality deck.

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

Use `scripts/render_pdf_pages.py` to render PDF pages into PNGs if page images do not exist. Then crop local regions with `scripts/crop_pdf_regions.py`.

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

Only crop figures/tables/algorithms that are useful for the talk. Avoid full-page screenshots unless the user explicitly requests them.

### 3. Slide Planning

Generate `intermediate/slide_outline.md` first. Default academic structure:

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

Then create `intermediate/slide_specs.json` for deterministic rendering. Use `references/slide_spec_schema.md`.

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

### 4. Slide Design

Use restrained academic design. Respect `style` in `slide_specs.json` when present:

- primary color default `#2563EB`;
- accent color default `#DC2626`;
- neutral color default `#6B7280`;
- title font default `Arial`;
- body font default `Arial`;
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

### 5. PPTX/HTML Rendering

Use available presentation tooling if present. Otherwise use:

```powershell
python scripts/build_pptx_from_spec.py --spec intermediate/slide_specs.json --out paper_ppt_project
```

The script generates:

- `final_presentation.pptx`
- `final_presentation.html`
- `speaker_notes.md`

### 6. Speaker Notes

Each slide must have notes. Notes should not simply repeat bullets. Include:

- the core message of the slide;
- what part of the figure/table/algorithm to point at;
- transition from previous slide;
- one likely question or caveat when useful;
- source provenance.

### 7. Optional Generator/Discriminator Refinement Loop

When the user asks for iterative improvement, professor-style review, adversarial review, or a more polished final deck, run a generator-reviewer loop.

Read these references when deeper guidance is needed:

- `references/generator_discriminator_loop.md`
- `references/academic_presentation_agent.md`
- `references/refinement_loop.md`
- `references/reviewer_rubric.md`

Use:

```powershell
python scripts/refine_presentation_loop.py --project paper_ppt_project --rounds 3 --target-score 8.5
```

The loop creates:

- `runs/round_01/`, `runs/round_02/`, ...
- `reviewer_report.json`
- `reviewer_report.md`
- `revision_plan.md`
- `final/final_presentation.pptx`
- `final/final_presentation.html`
- `final/speaker_notes.md`
- `improvement_history.md`

The bundled script provides deterministic structural review and automatic cleanup revisions. For true expert review, act as the reviewer yourself: inspect `paper_analysis.md`, `figures_index.md`, `slide_specs.json`, and `final_presentation.html`; then write sharper revision tasks before the next generator pass.

Run 3-5 rounds by default. Stop earlier if all key scores reach 9/10, if the user is satisfied, or if the score no longer improves.

## Quality Gates

Before final response, verify:

- PPTX opens structurally: ZIP test passes and slide XML parses;
- no full-page PDF screenshots are used unless requested;
- all cropped visuals have source paper/page in `figures_index.md`;
- slide text is not a wall of text;
- speaker notes exist for every slide;
- if refinement was requested, `reviewer_report.md`, `revision_plan.md`, and `improvement_history.md` exist;
- final response includes absolute paths to PPTX, HTML, and notes.

## Failure Handling

- If PDF text extraction is poor, render pages and use visual/caption-based analysis; tell the user OCR may be needed.
- If figure auto-cropping is unreliable, crop manually from rendered pages and document it.
- If no PPTX library exists, use the bundled OOXML renderer script.
- If the paper is very long or multi-paper input is large, first create a 12-15 slide version and save deeper notes separately.
