# Coordination With Existing Skills

Use this reference when deciding whether to call other skills.

## Paper Understanding

Prefer a paper-reading or literature-review skill when available:

- `nature-reader`: structured reading of academic papers.
- `research-lit` or `comm-lit-review`: literature-review framing and related-work analysis.
- domain-specific skills: stronger vocabulary and limitations for a field.

Expected output to feed this skill:

- problem;
- method;
- equations/model;
- algorithm;
- experiment setup;
- results;
- limitations.

## Slide Design

Use a mature slide-design skill when the user prioritizes visual quality:

- `baoyu-slide-deck`: professional image-based slide deck generation.
- presentation plugin/tools: editable PPTX generation if available.

Recommended handoff:

1. Use this skill to create `paper_analysis.md`, `figures_index.md`, and `slide_specs.json`.
2. Use design skill to polish visual style or generate slide images.
3. Keep `speaker_notes.md` and `source_map.md` from this skill for research traceability.

## Domain Skills

When a paper is in a specific domain, use domain skills to improve interpretation:

- TSN/DetNet/WAN: `tsn-paper-to-presentation`.
- ML/AI: ML paper writing/review skills.
- Grant/proposal paper: grant or proposal skills.

Do not let design skills override factual provenance.
