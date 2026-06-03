# Slide Spec Schema

Use this JSON shape for `intermediate/slide_specs.json`.

```json
{
  "title": "Deck title",
  "subtitle": "Optional subtitle",
  "author": "Optional presenter",
  "date": "YYYY-MM-DD",
  "language": "zh",
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
