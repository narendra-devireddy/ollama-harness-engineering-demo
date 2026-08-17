# Ollama Harness Engineering Demo

A demo project for showing the core claim of harness engineering:

> A normal model with good feedforward guides and feedback sensors can beat a stronger model with a weak or missing harness.

The project is designed around Ollama Cloud so the same runner can compare models such as `gpt-oss:20b` and `gpt-oss:120b` through either local Ollama cloud offload or direct `https://ollama.com` API access.

## Demo Thesis

The comparison should avoid vague “which answer feels better?” judging. Instead, every use case should have deterministic checks, approved fixtures, and a small amount of semantic judging only where necessary.

| Lane | Model | Harness | Expected lesson |
| --- | --- | --- | --- |
| Strong model, bad harness | `gpt-oss:120b` | bare prompt, minimal checks | Produces plausible answers but drifts, misses constraints, or creates fragile code. |
| Normal model, good harness | `gpt-oss:20b` | specs, examples, tools, tests, repair loop | Produces more deployable work because the environment narrows the task and catches mistakes. |

## Recommended Use Cases

### 1. API Contract Change

Ask both lanes to add a new field to an existing API while preserving backward compatibility.

Why it works:
- Bad harness often updates happy-path code but misses schema docs, tests, fixtures, or compatibility edge cases.
- Good harness can include OpenAPI diff checks, contract tests, golden JSON fixtures, and migration rules.

Signals:
- Contract tests pass.
- Existing fixtures remain unchanged unless explicitly approved.
- No breaking API diff.
- Coverage touches the changed behavior.

### 2. Bug Fix With Misleading Symptom

Give the model a failing test and logs where the obvious fix is wrong.

Why it works:
- Strong un-harnessed models may patch the symptom.
- Harnessed models can be forced through reproduction, root-cause notes, regression tests, and mutation checks.

Signals:
- New regression test fails before the fix and passes after.
- No broad try/catch or hardcoded workaround.
- Mutation survives are below threshold.

### 3. Architecture Boundary Enforcement

Ask for a feature that tempts the model to import directly across layers.

Why it works:
- The harness makes architecture executable, not just aspirational.
- A smaller model can succeed by staying inside rails.

Signals:
- Import graph / dependency-cruiser / custom AST checks pass.
- Domain layer has no framework imports.
- Adapters contain IO concerns.

### 4. Data Transformation With Approved Fixtures

Ask for messy input normalization, such as invoices, support tickets, or incident logs.

Why it works:
- Good behavior harness can rely on approved input/output fixtures.
- The judge can be deterministic: exact expected JSON, schema validation, edge-case fixtures.

Signals:
- Schema validation.
- Golden fixture match.
- Edge cases: missing fields, ambiguous dates, duplicate entities.

### 5. UI Flow Repair

Ask models to fix a small web app flow, such as filtering, optimistic update rollback, or keyboard navigation.

Why it works:
- Bad harness stops at code compiling.
- Good harness uses Playwright flow tests, accessibility checks, and screenshot diff thresholds.

Signals:
- Playwright tests pass.
- Axe/accessibility checks pass.
- Visual diff below threshold.

## Suggested First Demo

Start with **Data Transformation With Approved Fixtures**.

It is the clearest harness story because we can make quality measurable without building a large app. The normal model receives:
- A concise task spec.
- JSON schema.
- 8-12 approved fixtures.
- A repair loop that feeds validation errors back into the model.
- A final deterministic score.

The strong model receives:
- A plain natural-language prompt.
- No schema feedback until final scoring.

That produces an easy stage demo: same task, different harness, visible scoreboard.

## Ollama Cloud Setup

Direct hosted API mode:

```bash
export OLLAMA_API_KEY=your_api_key
export OLLAMA_HOST=https://ollama.com
```

Local Ollama cloud-offload mode:

```bash
ollama signin
ollama pull gpt-oss:20b-cloud
ollama pull gpt-oss:120b-cloud
```

Ollama docs describe cloud models as remote-executed models that can be used from local Ollama tooling, and direct API access as `https://ollama.com/api` with bearer authentication.

## Planned CLI

```bash
harness-demo run --case invoice-normalization --lane normal-good-harness
harness-demo run --case invoice-normalization --lane strong-bad-harness
harness-demo compare --case invoice-normalization
```

## Repository Shape

```text
src/harness_demo/       Python runner and scoring code
cases/                  Demo use cases with specs, prompts, schemas, fixtures
harness/                Reusable guides, sensors, and repair-loop templates
reports/                Generated scorecards
```

## Sources

- Martin Fowler: Harness engineering for coding agent users, 02 April 2026: https://martinfowler.com/articles/harness-engineering.html
- Ollama Cloud docs: https://docs.ollama.com/cloud
- Ollama API introduction: https://docs.ollama.com/api/introduction
