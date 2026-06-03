# Reviewer Rubric

Use this rubric when acting as the judge/reviewer in the generator-reviewer loop.

Score each dimension from 1 to 10:

- Paper understanding: Does the deck explain the real research problem, method, experiments, and limitations?
- Narrative flow: Does the story move from motivation to method to evidence to takeaways?
- Figure selection: Are figures/tables/algorithms relevant, readable, and placed on the right slides?
- Experimental interpretation: Do result slides explain baselines, metrics, settings, and what the result proves?
- Slide design: Are text density, figure size, layout, and title hierarchy suitable for a group meeting?
- Speaker notes: Can a student use the notes to speak naturally and answer likely questions?
- Expert readiness: Would a senior professor consider this presentation clear and defensible?

Reviewer behavior:

- Be strict and specific.
- Prefer actionable revision tasks over vague comments.
- Flag missing evidence, overstated claims, unreadable figures, and shallow limitations.
- Do not invent paper facts. If uncertain, request source verification.

Recommended JSON output:

```json
{
  "overall_score": 7.5,
  "dimensions": {
    "paper_understanding": 8,
    "narrative_flow": 7,
    "figure_selection": 8,
    "experimental_interpretation": 7,
    "slide_design": 6,
    "speaker_notes": 7,
    "expert_readiness": 7
  },
  "major_issues": [],
  "revision_tasks": [
    {
      "slide": 8,
      "priority": "high",
      "action": "Explain the algorithm input, output, state/action/reward, and stopping condition."
    }
  ]
}
```
