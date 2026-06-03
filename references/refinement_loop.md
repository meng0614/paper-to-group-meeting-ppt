# Generator-Reviewer Refinement Loop

Use this reference when the user asks for iterative improvement, adversarial review, professor-style critique, or a polished final deck.

## Roles

Generator:

- creates or revises `slide_specs.json`;
- selects figures/tables/algorithms;
- generates PPTX/HTML/speaker notes;
- applies revision tasks.

Reviewer/Judge:

- acts as a strict senior professor;
- reviews paper understanding, narrative, evidence, experiments, layout, and notes;
- produces `reviewer_report.json`, `reviewer_report.md`, and `revision_plan.md`.

## Loop

```text
initial slide_specs.json
  -> build PPTX/HTML/notes
  -> reviewer report
  -> revision plan
  -> revised slide_specs.json
  -> next round
```

Stop when:

- target score is reached;
- maximum rounds are reached;
- two rounds produce negligible improvement.

## Deterministic Script

Run:

```bash
python scripts/refine_presentation_loop.py --project output_dir --rounds 3 --target-score 8.5
```

The script creates:

```text
runs/
  round_01/
    final_presentation.pptx
    final_presentation.html
    speaker_notes.md
    reviewer_report.json
    reviewer_report.md
    revision_plan.md
  round_02/
final/
  final_presentation.pptx
  final_presentation.html
  speaker_notes.md
improvement_history.md
```

The bundled script performs deterministic structural review and automatic cleanup revisions. For deeper expert critique, have an AI reviewer read `reviewer_rubric.md`, inspect `final_presentation.html`, `slide_specs.json`, `paper_analysis.md`, and `figures_index.md`, then update the revision plan before the next generator pass.
