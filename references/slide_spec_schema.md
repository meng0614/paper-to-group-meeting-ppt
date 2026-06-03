# Slide Spec Schema

Use this JSON shape for `intermediate/slide_specs.json`.

```json
{
  "title": "Deck title",
  "subtitle": "Optional subtitle",
  "author": "Optional presenter",
  "date": "YYYY-MM-DD",
  "language": "zh",
  "style": {
    "primary_color": "2563EB",
    "accent_color": "DC2626",
    "neutral_color": "6B7280",
    "title_font": "Arial",
    "body_font": "Arial",
    "title_size": 32,
    "body_size": 20,
    "layout": "auto",
    "animation": "disable"
  },
  "refinement": {
    "last_reviewer_score": 7.8,
    "target_score": 8.5
  },
  "slides": [
    {
      "kind": "cover | section | content | figure | algorithm | result | matrix | closing",
      "title": "Assertion headline",
      "subtitle": "Optional",
      "bullets": ["2-5 short points"],
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

## Layout Guidance

- `cover`: title, subtitle, and 2-3 framing bullets.
- `section`: chapter divider for a paper or major part.
- `content`: bullets only or light visual.
- `figure`: mechanism/system/model figure with explanation bullets.
- `algorithm`: pseudocode image with inputs, outputs, loop logic, and complexity/intuition.
- `result`: plot/table image with metrics, baselines, and interpretation.
- `matrix`: comparison table.
- `closing`: final takeaways and discussion questions.

## Style Configuration

Generator must follow `style` when present:

- `primary_color`: default `2563EB`;
- `accent_color`: default `DC2626`;
- `neutral_color`: default `6B7280`;
- `title_font`: default `Arial`;
- `body_font`: default `Arial`;
- `title_size`: 28-36 recommended;
- `body_size`: 18-24 recommended;
- `layout`: `single-center`, `left-right`, `figure-first`, `auto`, or `custom`;
- `animation`: `enable`, `disable`, or `custom`.

## Figure Size Rules

- Wide plots: image top or center, 60-75% slide width.
- Tall algorithms: image right side, 40-50% slide width.
- System diagrams: image right side or full width depending on complexity.
- Tables: use full width if dense.

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
