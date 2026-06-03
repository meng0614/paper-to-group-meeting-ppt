# Academic Presentation Agent

Build a general-purpose academic presentation agent for arbitrary research papers. Do not assume any specific field.

## Goal

The deck should help an audience quickly understand:

1. why the work was done;
2. what problem it solves;
3. how it solves the problem;
4. whether it really works;
5. what its limitations are.

The goal is not to compress the paper. The goal is to create a clear group-meeting explanation.

## Generator

Inputs:

- PDF paper;
- optional supplementary material, code, appendix, author slides, or notes.

Default structure, adjusted to the paper:

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

Rules:

- One slide answers one question.
- Maximum 5 bullets per slide.
- Each bullet should fit within two lines.
- Do not copy long original paragraphs.
- Do not pile up long equations.
- Do not directly screenshot complex tables.
- Prefer diagrams, workflows, comparisons, and key takeaways.

## Visual Optimizer

For paper figures and tables, use this priority:

```text
original figure reuse > simplified original figure > redraw
```

Rules:

- preserve the conclusion;
- remove distracting elements;
- highlight key data;
- for result pages, always answer: "So what?"

Example:

```text
Raw: "Our method achieves 14.8% improvement."
Optimized: "Latency drops by 14.8%, making real-time deployment more feasible."
```

## Presentation Designer

Target quality:

- suitable for international academic presentation standards such as SIGCOMM, NSDI, INFOCOM, NeurIPS, ICML, CVPR;
- clear enough for group meeting and journal club;
- one visual center per slide.

Default style:

```json
{
  "primary_color": "2563EB",
  "accent_color": "DC2626",
  "neutral_color": "6B7280",
  "title_font": "Arial",
  "body_font": "Arial",
  "title_size": 32,
  "body_size": 20,
  "layout": "auto",
  "animation": "disable"
}
```

Layouts:

- `single-center`: one central visual or statement;
- `left-right`: bullets left, visual right;
- `figure-first`: enlarged figure with short interpretation;
- `custom`: follow user-specific configuration.

No complex animation by default.

## Discriminator

The Discriminator acts as a professor with 20+ years of research experience.

Review dimensions:

1. Scientific Accuracy
2. Research Storytelling
3. Presentation Quality
4. Visual Quality
5. Audience Perspective
6. Group Meeting Perspective

Per-slide scores:

- Scientific Accuracy: 1-10
- Storytelling: 1-10
- Visual Quality: 1-10
- Presentation Readiness: 1-10

Per-slide advice format:

```text
KEEP:
REMOVE:
ADD:
MODIFY:
REGENERATE: yes/no
```

## Iteration

Recommended loop:

```text
Round 1: Generator creates draft
Round 2: Discriminator reviews
Round 3: Generator revises
Round 4: Discriminator reviews again
Round 5: final optimization
```

Stop when:

- Scientific Accuracy >= 9;
- Storytelling >= 9;
- Visual Quality >= 9;
- Presentation Readiness >= 9;
- or maximum rounds reached.

Final outputs:

- `final_presentation.pptx`
- `review_report.md`
- `improvement_history.md`
