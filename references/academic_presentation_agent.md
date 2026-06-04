# Academic Presentation Agent

Build a general-purpose academic presentation agent for arbitrary research papers. Do not assume any specific field.

## Goal

The deck should help an audience quickly understand:

1. why the work was done;
2. what problem it solves;
3. how it solves the problem;
4. whether it really works;
5. what its limitations are.

The goal is not to compress the paper. The goal is to create a clear group-meeting explanation. The agent should behave like a McKinsey consultant, a top-conference author, and a professional presentation designer.

Use **Presentation-first / Visual-first** thinking. For every slide, first answer:

```text
Story Phase:
Problem / Challenge / Idea / Method / Result / Takeaway

One Message:
The one core claim this slide should deliver.

Audience Takeaway:
If the audience sees this slide for only 5 seconds, what should they remember?

Page Goal:
What should the audience understand if they see this slide for only 5 seconds?

Visual:
What visual form best conveys that goal?
The visual subject must occupy at least 40% of the slide.

Content:
What minimal text is needed to support the visual?
```

The slide should be generated only after this storyboard is clear.

## Design Philosophy

- One Slide One Message.
- Visual First: every non-cover slide has a visual subject covering at least 40% of the page.
- Visual Hierarchy: title > visual > explanation.
- Whitespace First: do not fill every empty region.
- Story First: Problem -> Challenge -> Idea -> Method -> Result -> Takeaway.
- Audience First: optimize for the 5-second memory.
- Layout Quality: prefer 15 clear slides over 10 crowded slides.

When a reference PPT is provided, learn only design philosophy: layout rhythm, whitespace, density, visual hierarchy, and story pacing. Do not copy colors, fonts, or theme.

Concrete patterns to learn from strong technical decks:

- stable master frame: repeated title zone, section label, page marker, and subtle divider/rail;
- clear title hierarchy: title is visually dominant and states the message;
- visual-text zoning: main visual and explanation text live in separate zones;
- disciplined whitespace: margins and empty regions are preserved intentionally;
- limited color roles: colors have roles rather than decorative randomness;
- chapter rhythm: repeated orientation elements guide the audience;
- technical visual priority: use diagrams, workflows, timelines, comparison panels, and plots before prose.

## Slide Architect

Before rendering slides, add a Slide Architect pass.

The Slide Architect decides:

- how many slides the talk needs;
- how much content each slide can safely carry;
- which layout is appropriate for each slide.

Principle:

```text
Prefer more slides over dense slides.
Do not fix overload by shrinking fonts.
```

If a section is complex, split it:

- Method -> Method Overview / Method Details / Method Example
- Experiment -> Experimental Setup / Experimental Results / Experimental Analysis
- Result -> Main Result / Result Analysis / So What

## Layout Validator

Before final output, automatically check:

1. Text Overflow
2. Text Overlap
3. Image Overlap
4. Chart Overflow
5. Object Collision
6. Font Readability
7. Content Overload

If any check fails, repair in this order:

1. Split pages.
2. Adjust layout.
3. Simplify content.
4. Adjust font size only as a last resort.

The final deck must include `layout_check_report.md`.

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
- Avoid text-only Background, Problem, Method, Algorithm, Experiment, and Result slides.
- For algorithm slides, redraw pseudocode as a decision flow, state transition, or module relation.
- For result slides, redraw or simplify charts when possible and annotate the "So What?".

## Visual-first Slide Types

Background:

- Use application scenario, system architecture, industry schematic, statistics, or typical-case visual.
- Visual area should be at least 40% of the slide.

Problem Statement:

- Use Existing vs Paper Setting comparison, bottleneck, mismatch, or constraint conflict.
- Do not merely list problems.

Method:

- Use framework, pipeline, workflow, or architecture diagram.
- The audience should understand the method overview in 30 seconds.

Algorithm:

- Use flowchart, decision process, state transition, or module relationship.
- Do not directly paste pseudocode unless the user explicitly asks.

Experiment:

- Show validation logic: setup -> baselines -> metrics -> claim.
- Avoid dense parameter tables as the main visual.

Results:

- Keep the core trend.
- Remove irrelevant curves.
- Mark best result and key improvement percentage.
- Every chart must answer "So What?".

Takeaways:

- State maximum contribution.
- State maximum novelty.
- State maximum limitation.

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
  "primary_color": "111827",
  "secondary_color": "2563EB",
  "accent_color": "DC2626",
  "neutral_color": "6B7280",
  "light_color": "F8FAFC",
  "title_font": "Microsoft YaHei",
  "body_font": "Microsoft YaHei",
  "title_size": 32,
  "body_size": 20,
  "layout": "auto",
  "design_system": "academic-rail",
  "animation": "disable"
}
```

Layouts:

- `visual-first`: choose comparison/pipeline/flow/result visual before text;
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
