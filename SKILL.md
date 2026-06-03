---
name: paper-to-group-meeting-ppt
description: Generate a simple academic group-meeting presentation from one or more research paper PDFs. Use when the user asks to turn arbitrary literature PDFs into a paper-reading PPT, group meeting slides, literature sharing deck, journal club presentation, or wants paper understanding plus cropped figures/tables/algorithms, PPTX/HTML output, and speaker notes.
---

# Paper to Group Meeting PPT

Create a research group-meeting deck from academic PDFs. The skill's core promise is:

```text
paper understanding -> evidence extraction -> polished slide layout -> speaker notes
```

The output should be a usable first draft for a human presenter, not merely a paper summary.

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
```

## Workflow

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

Generate `intermediate/slide_outline.md` first. Default single-paper structure:

1. Cover
2. What problem does the paper solve?
3. Why is the problem difficult?
4. Core idea in one picture
5. System/model overview
6. Method module 1
7. Method module 2
8. Algorithm or optimization process
9. Experimental setup
10. Main result 1
11. Main result 2
12. Ablation/sensitivity/comparison if available
13. Contributions
14. Limitations
15. Discussion questions

For multiple papers, use: per-paper brief reading -> comparison matrix -> shared takeaways.

Then create `intermediate/slide_specs.json` for deterministic rendering. Use `references/slide_spec_schema.md`.

### 4. Slide Design

Use restrained academic design:

- assertion headlines;
- 16:9 layout;
- white or very light gray content slides;
- dark chapter divider only when useful;
- 2-5 bullets per slide;
- cropped paper figure should normally occupy 45-70% of the slide;
- algorithm slides: keep pseudocode large and readable;
- result slides: enlarge plots first, then add interpretation text;
- do not over-decorate.

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

## Quality Gates

Before final response, verify:

- PPTX opens structurally: ZIP test passes and slide XML parses;
- no full-page PDF screenshots are used unless requested;
- all cropped visuals have source paper/page in `figures_index.md`;
- slide text is not a wall of text;
- speaker notes exist for every slide;
- final response includes absolute paths to PPTX, HTML, and notes.

## Failure Handling

- If PDF text extraction is poor, render pages and use visual/caption-based analysis; tell the user OCR may be needed.
- If figure auto-cropping is unreliable, crop manually from rendered pages and document it.
- If no PPTX library exists, use the bundled OOXML renderer script.
- If the paper is very long or multi-paper input is large, first create a 12-15 slide version and save deeper notes separately.
