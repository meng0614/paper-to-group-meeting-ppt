# Paper to Group Meeting PPT

Generate a high-quality academic group-meeting presentation from a research paper PDF.

This skill is a general Academic Presentation Agent. It is not tied to any specific discipline. It can be used for systems, networking, AI, medicine, biology, social science, and other academic papers.

The workflow:

```text
paper understanding -> visual evidence optimization -> slide design -> professor review -> refined presentation
```

It does not only summarize a paper. It helps an AI agent read the paper, extract useful visual evidence such as figures, tables, algorithms, and result plots, design an academic slide deck, and produce speaker notes for a group meeting or journal-club style presentation.

It supports a Generator/Discriminator refinement loop:

```text
Generator -> Reviewer/Judge -> Revision Plan -> Generator
```

The Discriminator acts like a strict senior professor and critiques the deck from the perspectives of scientific accuracy, research storytelling, presentation quality, visual quality, audience perspective, and group-meeting suitability.

## What It Generates

Expected output for each paper:

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
  runs/
  final/
  review_report.md
  improvement_history.md
```

## Skill Capabilities

- Understand the paper structure: problem, motivation, method, experiments, results, limitations.
- Extract and crop useful visual evidence from PDFs.
- Avoid full-page screenshots unless explicitly requested.
- Generate editable PPTX from a slide specification.
- Generate HTML preview and speaker notes.
- Coordinate with existing paper-reading and slide-design skills when available.

## Included Scripts

```text
scripts/render_pdf_pages.py       Render PDF pages to PNG with pdftoppm.
scripts/crop_pdf_regions.py       Crop figures/tables/algorithms from rendered pages.
scripts/create_10_slide_spec_template.py Create a standard 10-slide group-meeting spec.
scripts/build_pptx_from_spec.py   Build PPTX, HTML preview, and speaker notes from slide_specs.json.
scripts/refine_presentation_loop.py Run generator-reviewer-reviser refinement rounds.
```

## Dependencies

Required:

- Python 3.9+
- Pillow

Optional but recommended:

- `pdftoppm` from Poppler or TeX Live, for PDF page rendering.

## Usage Inside an AI Skill Runtime

Install this folder as a skill. Then ask:

```text
Please turn this research paper PDF into a group-meeting presentation.
Include paper understanding, cropped figures/tables/algorithms, PPTX, HTML preview, and speaker notes.
```

The skill instructions in `SKILL.md` define the complete workflow.

## Manual Script Usage

Render pages:

```bash
python scripts/render_pdf_pages.py paper.pdf --out output/pages --dpi 140
```

Crop regions:

```bash
python scripts/crop_pdf_regions.py --pages output/pages --spec crop_specs.json --out output/figures
```

Build slides:

```bash
python scripts/build_pptx_from_spec.py --spec output/intermediate/slide_specs.json --out output
```

Create the default 10-slide group-meeting structure:

```bash
python scripts/create_10_slide_spec_template.py --project output --lang zh
```

Run iterative refinement:

```bash
python scripts/refine_presentation_loop.py --project output --rounds 3 --target-score 8.5
```

The Discriminator report scores every slide:

```text
Scientific Accuracy: 1-10
Storytelling: 1-10
Visual Quality: 1-10
Presentation Readiness: 1-10
```

It also gives:

```text
KEEP
REMOVE
ADD
MODIFY
REGENERATE
```

This creates:

```text
output/runs/round_01/reviewer_report.md
output/runs/round_01/revision_plan.md
output/final/final_presentation.pptx
output/final/final_presentation.html
output/final/speaker_notes.md
output/improvement_history.md
```

## Limitations

- Arbitrary PDFs can be difficult: scanned PDFs, bad captions, and unusual layouts may require manual crop adjustment.
- The included PPTX renderer is intentionally simple. For highly polished visual design, hand off the slide specs and cropped figures to a mature slide-design skill.
- The output is a strong first draft for research discussion, not a guaranteed final conference presentation.
- The bundled reviewer loop is a deterministic structural judge. For true expert-level critique, combine it with an AI reviewer using `references/reviewer_rubric.md`.

## License

MIT
