# Paper to Group Meeting Presentation Agent

Generate a high-quality academic group-meeting HTML report and editable PowerPoint deck from a research paper PDF.

This skill is a general Academic Presentation Agent. It is not tied to any specific discipline. It can be used for systems, networking, AI, medicine, biology, social science, and other academic papers.

The default v3 workflow:

```text
Research Understanding Engine v3 -> Storyline Extraction -> Figure-Centric Understanding -> Theory/Method/Experiment Teaching Pages -> enhanced caption-aware figure extraction -> HTML report + editable PPTX -> layout / figure validators -> professor review artifacts
```

It does not only summarize a paper. The default strategy is **Presentation-first / Visual-first**: every section starts with Story Phase, One Message, 5-second takeaway, Visual, and Content. The report should help someone who has not read the paper understand the motivation, problem, core idea, why it works, and whether experiments support it in 10-15 minutes.

The v3 generator borrows the strongest ideas from Nature-style paper presentation skills: build the research story before slides, explain Why / What / How / Why Effective / How Verified, bind results to claims, and close with contribution, mechanism, and boundary. It now adds teaching-first research understanding: Research Gap / Motivation / Key Insight / Theory / Method / Validation Logic / Contribution are extracted before slide design; figures are assigned roles such as motivation figure, core theory figure, method framework figure, and main result figure. Figure extraction still renders at high DPI, locates caption-linked regions, trims to visual content, pads, upscales when needed, and writes a figure-quality report.

The design philosophy is:

```text
One Slide One Message
Visual First: visual subject area >= 40%
Visual Hierarchy: title > visual > explanation
Whitespace First
Story First: Problem -> Why Existing Work Fails -> Key Insight -> Theory -> Method -> Experiment Logic -> Results -> Takeaways
Audience First: what should the audience remember in 5 seconds?
Layout Quality: add pages instead of crowding content
```

When a polished reference PPT is provided, the skill learns design philosophy only, not colors or fonts. Transferable patterns include:

- stable master frame: repeated title zone, section label, page marker, and subtle divider/rail;
- clear title hierarchy: the slide headline carries the message;
- visual-text zoning: main visual and explanation text have predictable zones;
- disciplined whitespace: margins and empty space are preserved;
- limited color roles: primary, structural accent, highlight, neutral annotation;
- chapter rhythm: repeated orientation elements help the audience follow the talk;
- technical visual priority: diagrams, workflows, timelines, comparison panels, and plots before paragraphs.

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
    research_understanding.json
    domain_primer.md
    motivation_chain.json
    related_work_matrix.json
    gap_analysis.json
    contribution_cards.json
    method_model.json
    why_effective.md
    experiment_cards.json
    result_to_claim_matrix.json
    limitation_risks.json
    research_story_brief.md
    storyline_extraction.md
    figure_roles.md
    theory_model.md
    experiment_logic.md
    professor_gate.md
    understanding_review.md
    paper_analysis.md
    figures_index.md
    slide_outline.md
    visual_storyboard.md
    slide_specs.json
    source_map.md
    language_check_report.md
  final_presentation_generated.html
  final_presentation.html
  final_presentation_generated.pptx
  final_presentation.pptx
  layout_check_report.md
  figure_quality_report.md
  speaker_notes.md
  runs/
  final/
  review_report.md
  improvement_history.md
```

## Skill Capabilities

- Build a Research Understanding Engine output before slide design: Why / What / How / Why Effective / How Verified.
- Reconstruct the paper as a teaching storyline: Research Gap, Motivation, Key Insight, Theory, Method, Validation Logic, and Contribution.
- Identify figure roles: Motivation Figure, Core Theory Figure, Method Framework Figure, Main Result Figure, setup/evidence figures, and table evidence.
- Compress theory sections with Lemma/Theorem/Corollary cues into Problem -> Assumption -> Key Derivation -> Final Insight.
- Convert method descriptions into visual flows such as Input -> Theory Factors -> Objective -> GRASP Search -> Local Search -> Output.
- Reconstruct experiment logic as Question -> Setup -> Evidence -> Conclusion for ablation, comparison, and scalability.
- Understand the paper structure: problem, motivation, method, experiments, results, limitations.
- Extract a motivation chain, related-work gap, contribution cards, method model, result-to-claim matrix, and reviewer caveats.
- Create a visual storyboard with Story Phase / One Message / 5-second takeaway / Visual / Content for every slide.
- Plan slide count and page capacity with a Slide Architect before rendering.
- Extract and crop useful visual evidence from PDFs.
- Redraw or simplify selected visuals as comparisons, pipelines, flows, and result bars.
- Validate layout before final output: text overflow, object collision, chart overflow, image overlap, and font readability.
- Avoid full-page screenshots unless explicitly requested.
- Generate a polished academic HTML report from a section specification.
- Generate an editable PPTX deck from the same section specification. Text, diagrams, result bars, and callouts are PowerPoint objects; the PPTX is not an HTML screenshot.
- Support MathJax formulas, pseudocode, foldable long text, scrollable tables, and dynamic result bars.
- Generate speaker notes.
- Rotate among figure-first, left-right, top-visual, flow, comparison, and result-focus layouts to avoid repetitive pages.
- Choose layouts by story phase: Problem/Challenge -> comparison or bottleneck; Idea/Method -> framework or pipeline; Result -> enlarged chart plus So What; Takeaway -> contribution/novelty/limitation.
- Check cropped figures for low resolution, likely incomplete crops, excessive whitespace, blur, and low contrast.
- Support multiple style presets: `nature-clean`, `conference-blue`, `minimal-dark`, and `warm-paper`.
- Prefer `pptxgenjs` when available for polished editable PPTX with speaker notes; fall back to the Python OOXML renderer when Node/pptxgenjs is unavailable.
- Coordinate with existing paper-reading and slide-design skills when available.
- Optionally use external figure extraction backends such as PDFFigures2, GROBID, PyMuPDF, or LayoutParser when installed. See `references/figure_extraction_backends.md`.

## Included Scripts

```text
scripts/render_pdf_pages.py       Render PDF pages to PNG with pdftoppm at PPT-readable DPI.
scripts/build_research_understanding.py Build source-grounded Research Understanding Engine v3 artifacts.
scripts/extract_reference_design_philosophy.py Learn reference PPT layout philosophy without copying colors/fonts.
scripts/crop_pdf_figures_by_caption.py Caption-aware figure cropper using pdftotext bbox coordinates.
scripts/crop_pdf_regions.py       Manual clean-box cropper with padding, trimming, and upscaling.
scripts/figure_quality_validator.py Check cropped figure readability and likely crop mistakes.
scripts/create_10_slide_spec_template.py Create a standard 10-slide group-meeting spec.
scripts/create_visual_first_spec_template.py Create a visual-first Page Goal/Visual/Content spec.
scripts/slide_architect.py       Split overloaded content before rendering.
scripts/build_html_report_from_spec.py Build final HTML report and speaker notes.
scripts/build_pptxgenjs_from_spec.js Build polished editable PPTX with style presets and speaker notes when pptxgenjs is available.
scripts/build_editable_pptx_from_spec.py Build editable PPTX from the same section spec.
scripts/html_layout_validator.py Validate HTML sections and generate layout_check_report.md.
scripts/build_pptx_from_spec.py   Optional compatibility PPTX renderer.
scripts/layout_validator.py       Optional PPTX-style layout validator.
scripts/refine_presentation_loop.py Run generator-reviewer-reviser refinement rounds.
scripts/generate_academic_presentation_legacy.py Legacy pre-v2 generator preserved for rollback/comparison.
scripts/build_research_understanding_legacy.py Legacy pre-v2 understanding engine preserved for rollback/comparison.
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
Include paper understanding, visual sections, figures/tables/algorithms, HTML report, editable PPTX, layout check, figure quality check, review report, and speaker notes.
```

The skill instructions in `SKILL.md` define the complete workflow.

## Manual Script Usage

One-command Academic Presentation Agent:

```bash
python scripts/generate_academic_presentation.py \
  --pdf paper.pdf \
  --project output/paper_ppt_project \
  --lang zh \
  --style nature-clean \
  --rounds 3 \
  --target-score 9
```

This creates the complete planning and rendering chain:

```text
intermediate/research_understanding.json
intermediate/slide_specs.json
intermediate/research_story_brief.md
intermediate/paper_analysis.md
final_presentation_generated.html
final_presentation_generated.pptx
layout_check_report.md
figure_quality_report.md
review_report.md
improvement_history.md
```

Language selection:

- `--lang zh`: generate Chinese visible slide/report content, while preserving paper titles, acronyms, and necessary technical terms. Long English source excerpts stay in notes and source artifacts.
- `--lang en`: generate English visible slide/report content and suppress Chinese template leakage.

Style selection:

- `--style nature-clean`: clean white academic talk, strong hierarchy.
- `--style conference-blue`: modern blue conference deck.
- `--style minimal-dark`: dark seminar/talk style.
- `--style warm-paper`: warmer editorial academic style.

Each run writes `language_check_report.md`; `PASS` means no long source-language prose is visible in the wrong language mode.

Run only the understanding layer:

```bash
python scripts/build_research_understanding.py \
  --pdf paper.pdf \
  --project output/paper_ppt_project \
  --lang zh
```

Render pages:

```bash
python scripts/render_pdf_pages.py paper.pdf --out output/pages --dpi 220
```

Crop figures by caption whenever possible:

```bash
python scripts/crop_pdf_figures_by_caption.py --pdf paper.pdf --pages output/pages --spec caption_crop_specs.json --out output/figures
```

If external scholarly extraction tools are installed, prefer them before manual screenshots:

- PDFFigures2: extracts scholarly figures, tables, captions, and figure boxes.
- GROBID coordinates: useful when TEI/JSON figure coordinates are available.
- PyMuPDF: useful for high-DPI clipped rendering once a clean rectangle is known.

Example caption spec:

```json
[
  {"file": "fig2_tas_vs_cedf.png", "page": 4, "label": "Fig. 2", "column": "right", "position": "above"}
]
```

Manual clean-box crop when caption detection is not enough:

```bash
python scripts/crop_pdf_regions.py --pages output/pages --spec crop_specs.json --out output/figures --padding 24 --trim --min-width 1000
```

Connected-component repair is a last-resort fallback for a single problematic figure. Do not batch-apply it to all crops, because it can merge nearby body text in two-column PDFs:

```bash
python scripts/crop_pdf_regions.py --pages output/pages --spec one_figure_crop.json --out output/figures --component-expand --search-pad 320 --min-width 1000
```

`crop_pdf_regions.py` now applies seed-aware edge cleanup by default. It tries to remove page headers, neighboring body text, and caption fragments while preserving the visual region around the original seed box. Disable it only for unusual multi-panel figures:

```bash
python scripts/crop_pdf_regions.py --pages output/pages --spec one_figure_crop.json --out output/figures --no-clean-edges
```

Check cropped figure quality:

```bash
python scripts/figure_quality_validator.py --figures output/figures --report output/figure_quality_report.md
```

Build HTML report:

```bash
python scripts/build_html_report_from_spec.py --spec output/intermediate/slide_specs.json --out output
```

Build editable PPTX:

```bash
python scripts/build_editable_pptx_from_spec.py --spec output/intermediate/slide_specs.json --out output
```

Learn reference PPT design philosophy without copying colors or fonts:

```bash
python scripts/extract_reference_design_philosophy.py --reference reference.pptx --out output/intermediate/reference_design_philosophy.json
```

Run Slide Architect before building:

```bash
python scripts/slide_architect.py \
  --spec output/intermediate/slide_specs.json \
  --out output/intermediate/slide_specs.architected.json \
  --report output/intermediate/slide_architect_report.md
```

Run HTML Layout Validator after building:

```bash
python scripts/html_layout_validator.py \
  --project output \
  --spec output/intermediate/slide_specs.architected.json \
  --html output/final_presentation_generated.html \
  --report output/layout_check_report.md
```

Create the default 10-slide group-meeting structure:

```bash
python scripts/create_10_slide_spec_template.py --project output --lang zh
```

Create a Visual-first academic talk structure:

```bash
python scripts/create_visual_first_spec_template.py --project output --lang zh
```

Each section in `slide_specs.json` should include:

```json
{
  "story_phase": "Problem | Challenge | Idea | Method | Result | Takeaway",
  "one_message": "The single core claim of this slide",
  "audience_takeaway": "What should the audience remember in 5 seconds?",
  "page_goal": "What should the audience understand in 5 seconds?",
  "visual_area_min": 0.4,
  "visual": {
    "type": "comparison | pipeline | flow | result_bar | concept"
  },
  "content": "Minimal text that supports the visual"
}
```

Visual-first rules:

- Do not copy the reference PPT's colors or fonts.
- Build the deck as Problem -> Why Existing Work Fails -> Key Insight -> Theory -> Method -> Experiment Logic -> Results -> Takeaways.
- Every slide should have one message and one visual center.
- The visual subject should occupy at least 40% of the page.
- Background slides should use scenario/system/statistics visuals, not text only.
- Problem slides should use Existing vs Paper Setting or bottleneck diagrams.
- Method slides should use framework, pipeline, workflow, or architecture diagrams.
- Algorithm slides should use flowcharts or decision flows instead of raw pseudocode.
- Experiment slides should show validation logic: setup -> baselines -> metrics -> claim.
- Result slides should simplify charts and mark So What, such as `Latency ↓ 25%`.
- Takeaways should state maximum contribution, maximum novelty, and maximum limitation.

Run iterative refinement:

```bash
python scripts/refine_presentation_loop.py --project output --rounds 3 --target-score 8.5
```

The Discriminator report scores every section:

```text
Scientific Accuracy: 1-10
Storytelling: 1-10
Readability: 1-10
Visual Hierarchy: 1-10
Visual-first Compliance: 1-10
Layout Safety: 1-10
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
output/runs/round_01/slide_architect_report.md
output/runs/round_01/layout_check_report.md
output/runs/round_01/figure_quality_report.md
output/final/final_presentation_generated.html
output/final/final_presentation.html
output/final/final_presentation_generated.pptx
output/final/final_presentation.pptx
output/final/speaker_notes.md
output/improvement_history.md
```

## Limitations

- Arbitrary PDFs can be difficult: scanned PDFs, bad captions, and unusual layouts may require manual crop adjustment.
- The editable PPTX renderer is deterministic and produces strong first-draft academic slides. Very complex figures may still need manual re-cropping or redrawing.
- The output is a strong first draft for research discussion, not a guaranteed final conference/report artifact.
- The bundled reviewer loop is a deterministic structural judge. For true expert-level critique, combine it with an AI reviewer using `references/reviewer_rubric.md`.

## License

MIT
