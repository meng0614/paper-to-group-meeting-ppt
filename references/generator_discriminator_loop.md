# Generator/Discriminator Paper PPT Loop

Use this reference when generating an academic group-meeting PPT with adversarial refinement.

## Generator Role

The Generator creates or revises the presentation from the paper PDF and intermediate analysis.

Default deck structure for a single paper:

1. Title, authors, affiliations
2. Background and motivation
3. Core research problem
4. Limitations of existing methods
5. Proposed method overview
6. Core algorithm/mechanism
7. Experimental design
8. Experimental results
9. Contributions
10. Limitations and future work

Rules:

- Use 2-5 bullets per slide.
- Keep each bullet concise, roughly 12-15 Chinese characters or one short English phrase when possible.
- Highlight key terms in wording, e.g. `CEDF`, `deadline curve`, `MAPPO-AC`, `TAS`, `CSQF`.
- Use cropped figures/tables/algorithms instead of full PDF pages.
- For complex plots, simplify the explanation: trend, baseline, key metric, and conclusion.
- Notes must include source provenance and a short explanation of how to present the slide.

## Discriminator Role

The Discriminator reviews the generated PPT like a senior professor.

Review dimensions:

- Scientific accuracy: Are methods, equations, figures, and claims faithful to the paper?
- Logic: Is the order background -> problem -> method -> experiment -> conclusion clear?
- Readability: Is each slide explainable in 45-60 seconds?
- Aesthetics: Are figure size, font hierarchy, color, and layout readable?
- Topic fit: Does the deck focus on the paper's central contribution?

For each slide, produce:

- concrete issues;
- improved bullets when useful;
- whether the slide must be regenerated;
- priority: high / medium / low.

## Loop Procedure

```text
Round 1:
  Generator creates first deck
  Discriminator reviews every slide
  Generator revises slide_specs.json and regenerates deck

Round 2-5:
  Repeat until the deck is scientifically accurate, logical, readable, and visually clean
```

Stop conditions:

- score >= target score;
- maximum rounds reached;
- two consecutive rounds improve by less than 0.3;
- user says to stop.

## Required Artifacts

```text
runs/round_01/
  final_presentation.pptx
  final_presentation.html
  speaker_notes.md
  reviewer_report.json
  reviewer_report.md
  revision_plan.md

final/
  final_presentation.pptx
  final_presentation.html
  speaker_notes.md

improvement_history.md
```

