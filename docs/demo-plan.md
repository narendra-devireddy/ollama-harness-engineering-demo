# Demo Plan

## Narrative

1. Show the two lanes.
2. Run a strong model with a bare prompt.
3. Run a normal model with guides, fixtures, validators, and a repair loop.
4. Compare objective scores.
5. Open the failed outputs to show how the harness caught mistakes earlier.

## What The Harness Contains

Feedforward guides:
- Task spec with non-negotiable constraints.
- Output schema.
- Examples and approved fixtures.
- Implementation rules.
- Definition of done.

Feedback sensors:
- JSON/schema validation.
- Fixture comparison.
- Unit tests.
- Static checks.
- Optional LLM judge for semantic qualities that deterministic tests cannot capture.

Steering loop:
- If a sensor fails, pass the failure back to the model with a narrow repair instruction.
- Cap repair attempts to keep the comparison fair.
- Persist every prompt, output, sensor result, and score.

## Initial Use Case Choice

Use `invoice-normalization` first because it is small, visual enough for a demo, and highly measurable.

Input: messy invoice text.
Output: normalized invoice JSON.
Hard parts: dates, totals, tax, vendor identity, line item normalization, missing fields.
