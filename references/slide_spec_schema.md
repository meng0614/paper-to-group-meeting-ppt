# Slide Spec Schema

Use this JSON shape for `intermediate/slide_specs.json`. The default renderers now produce both an HTML report and an editable PPTX deck. `slides` is still accepted for compatibility, but `sections` is preferred.

```json
{
  "title": "Deck title",
  "subtitle": "Optional subtitle",
  "author": "Optional presenter",
  "date": "YYYY-MM-DD",
  "language": "zh",
  "style": {
    "primary_color": "0E2557",
    "secondary_color": "4B649F",
    "accent_color": "FF0000",
    "neutral_color": "6B7280",
    "light_color": "F4F7FB",
    "title_font": "Microsoft YaHei",
    "body_font": "Microsoft YaHei",
    "title_size": 30,
    "body_size": 19,
    "layout": "reference-inspired",
    "animation": "disable",
    "reference_pptx": "optional reference PPT path"
  },
  "refinement": {
    "last_reviewer_score": 7.8,
    "target_score": 8.5
  },
  "planning": {
    "slide_architect": {
      "original_slide_count": 10,
      "planned_slide_count": 14,
      "rule": "Prefer splitting pages over shrinking fonts."
    }
  },
  "sections": [
    {
      "section": "Background | Problem | Method | Experiment | Results | Conclusion",
      "kind": "cover | section | background | problem | method | figure | algorithm | experiment | result | matrix | closing",
      "title": "Assertion headline",
      "subtitle": "Optional",
      "page_goal": "What the audience should understand in 5 seconds.",
      "visual": {
        "type": "comparison | pipeline | flow | result_bar | concept",
        "insight": "Main visual takeaway"
      },
      "content": "Minimal text needed to explain the visual.",
      "body": "Longer multi-line explanation for HTML report body.",
      "bullets": ["2-5 short points"],
      "formula": "E = mc^2",
      "pseudocode": "Algorithm text",
      "details": "Long text that will be folded under a details element.",
      "image": "figures/fig_01_framework.png",
      "table": {
        "columns": ["Paper", "Method"],
        "rows": [["A", "B"]]
      },
      "notes": "Speaker notes with source provenance."
    }
  ]
}
```

## HTML Report Layout Guidance

- `cover`: title, subtitle, and framing text.
- `section`: chapter divider for a paper or major part.
- `background`: visual scenario/system/statistics page; never text-only.
- `problem`: Existing vs paper setting, bottleneck, mismatch, or conflict diagram.
- `method`: framework, pipeline, workflow, or architecture diagram.
- `content`: bullets only or light visual.
- `figure`: mechanism/system/model figure with explanation bullets.
- `algorithm`: flowchart, decision flow, state transition, or module relation. Raw pseudocode may be embedded in a scrollable block.
- `experiment`: validation logic: setup -> baselines -> metrics -> claim.
- `result`: simplified chart with metrics, baselines, best result, improvement, and So What.
- `matrix`: comparison table.
- `closing`: maximum contribution, maximum novelty, maximum limitation, and discussion questions.

## Page Capacity Rules

The Slide Architect should run before rendering. It decides how many pages are needed and how much content each page may carry.

Default capacity:

- Background / Problem / Method / Algorithm / Experiment / Result: at most 2 bullets.
- Figure pages: at most 3 bullets.
- Closing pages: at most 3 bullets.
- Pipeline / flow visuals: at most 4 steps.
- Comparison visuals: at most 3 points per side.
- Result charts: at most 4 highlighted items.

If a page exceeds capacity, split it. Do not shrink fonts as the first response.

Preferred split patterns:

- Method -> Method Overview / Method Details / Method Example
- Algorithm -> Algorithm Intuition / Decision Flow / Feasibility Check
- Experiment -> Experimental Setup / Experimental Results / Experimental Analysis
- Result -> Main Result / Result Analysis / So What

## HTML Layout Validation

Before final output, generate `layout_check_report.md` with `scripts/html_layout_validator.py`.

Required checks:

- Text Overflow
- Text Overlap
- Image Overlap
- Chart Overflow
- Object Collision
- Font Readability
- Content Overload
- Scrollable/Foldable Long Content

Repair priority:

1. Split pages.
2. Adjust layout.
3. Simplify content.
4. Adjust font size only as a last resort.

## HTML and PPTX Output

Final outputs:

- `final_presentation_generated.html`
- `final_presentation.html`
- `final_presentation_generated.pptx`
- `final_presentation.pptx`
- `layout_check_report.md`
- `figure_quality_report.md`
- `review_report.md`
- `improvement_history.md`

HTML should support:

- MathJax formulas;
- pseudocode blocks;
- foldable long text through `<details>`;
- scrollable tables;
- dynamic result bars;
- one visual center per section.

The PPTX renderer should create editable PowerPoint objects:

- text boxes for titles, Page Goal, content, captions, and bullets;
- shape objects for comparison panels, pipelines, flow steps, and result bars;
- picture objects for paper figures, cropped diagrams, tables, and algorithms;
- varied layouts instead of repeating one left-image/right-text template.

Do not render the HTML page as a static image inside PowerPoint unless the user explicitly requests a screenshot deck.

## Visual-first Planning Fields

Every non-trivial slide should include:

- `page_goal`: the 5-second audience takeaway;
- `visual`: the main visual expression;
- `content`: the minimum text needed to support the visual.

Supported deterministic visual specs:

```json
{
  "visual": {
    "type": "comparison",
    "left_title": "Existing",
    "right_title": "This Work",
    "left": ["assumption A", "limitation B"],
    "right": ["new setting", "new capability"],
    "insight": "Why the comparison matters"
  }
}
```

```json
{
  "visual": {
    "type": "pipeline",
    "steps": [
      {"label": "Input", "detail": "what enters the method"},
      {"label": "Decision", "detail": "core mechanism"},
      {"label": "Output", "detail": "what guarantee/result is produced"}
    ],
    "insight": "30-second method overview"
  }
}
```

```json
{
  "visual": {
    "type": "result_bar",
    "items": [
      {"label": "Baseline", "value": 70},
      {"label": "Proposed", "value": 88, "highlight": true}
    ],
    "unit": "%",
    "so_what": "Scheduling Success ↑ 18%"
  }
}
```

## Style Configuration

Generator must follow `style` when present:

- `primary_color`: default `0E2557`;
- `secondary_color`: default `4B649F`;
- `accent_color`: default `FF0000`;
- `neutral_color`: default `6B7280`;
- `light_color`: default `F4F7FB`;
- `title_font`: default `Microsoft YaHei`;
- `body_font`: default `Microsoft YaHei`;
- `title_size`: 28-36 recommended;
- `body_size`: 18-24 recommended;
- `layout`: `visual-first`, `reference-inspired`, `single-center`, `left-right`, `figure-first`, `auto`, or `custom`;
- `animation`: `enable`, `disable`, or `custom`.

## Figure Size Rules

- Wide plots: image top or center, 60-75% slide width.
- Tall algorithms: image right side, 40-50% slide width.
- System diagrams: image right side or full width depending on complexity.
- Tables: use full width if dense.
- Crop figures from high-DPI PDF renders, normally 220 DPI or higher.
- Expand crop boxes with padding. Tight edge contact is a likely incomplete crop.
- Check every cropped image with `figure_quality_validator.py`; low-resolution or edge-touching figures should be re-cropped before final delivery.

## Speaker Notes Rules

Each slide's `notes` field should include:

1. what to say first;
2. how to explain the image/table/algorithm;
3. the transition to the next slide;
4. source paper and page/section.

## Refinement Rules

When using the generator-reviewer loop:

- keep `slides` as the source of truth;
- store reviewer scores under `refinement`;
- do not delete slide provenance while revising;
- convert reviewer comments into concrete changes to `kind`, `title`, `bullets`, `image`, and `notes`;
- prefer improving the existing deck over regenerating everything from scratch.
