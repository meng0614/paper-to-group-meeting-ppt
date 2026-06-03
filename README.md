# Paper to Group Meeting PPT

Generate a simple academic group-meeting presentation from a research paper PDF.

This skill is designed for research workflows:

```text
paper understanding -> evidence extraction -> slide design -> speaker notes
```

It does not only summarize a paper. It helps an AI agent read the paper, extract useful visual evidence such as figures, tables, algorithms, and result plots, design an academic slide deck, and produce speaker notes for a group meeting or journal-club style presentation.

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
scripts/build_pptx_from_spec.py   Build PPTX, HTML preview, and speaker notes from slide_specs.json.
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

## Limitations

- Arbitrary PDFs can be difficult: scanned PDFs, bad captions, and unusual layouts may require manual crop adjustment.
- The included PPTX renderer is intentionally simple. For highly polished visual design, hand off the slide specs and cropped figures to a mature slide-design skill.
- The output is a strong first draft for research discussion, not a guaranteed final conference presentation.

## License

MIT
