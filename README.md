# Ollama Harness Engineering Demo

A management-friendly demo showing why harness engineering matters and how the industry is moving from custom harnesses toward SDK abstractions and plug-and-play provider harnesses.

Core claim:

> A normal model inside a strong harness can beat a stronger model that is left to improvise.

This repo is built around a multi-agent incident response scenario because it makes the harness benefits visible: shared context, memory, tool control, validation, review, and observability.

## Demo Story

The demo runs the same incident through four lanes:

| Lane | Tooling | What it shows |
| --- | --- | --- |
| Raw model | Direct model call through Ollama Cloud / OpenAI-compatible endpoint | A strong model can produce a plausible but unsafe answer without controls. |
| Hand-built harness | Python orchestration + typed memory + sensors + repair loop | The mechanics of harness engineering are concrete and measurable. |
| SDK harness | Strands Agents | Agent runtime features such as tools, hooks, conversation management, memory, observability, and multi-agent patterns reduce custom plumbing. |
| Provider harness | DeepSeek harness candidate | Provider-specific quirks can become plug-and-play controls once packaged. |

The business message is simple:

> We are not betting on one model. We are building a controlled AI execution environment where models are replaceable and quality controls are reusable.

## Primary Use Case

### Multi-Agent Incident Response

Input: a production incident ticket, log snippets, service metadata, prior incident memory, and an approved runbook.

Agents:

- **Triage Agent**: extracts severity, impacted service, customer impact, and missing facts.
- **Log Investigator Agent**: searches evidence and identifies the likely fault.
- **Runbook Agent**: retrieves approved remediation steps and constraints.
- **Fix Planner Agent**: proposes the safest next action.
- **Reviewer Agent**: blocks unsafe fixes and checks rollback/completeness.

Shared memory:

- incident facts
- investigated evidence
- prior similar incident
- runbook constraints
- attempted actions
- reviewer objections
- final resolution plan

## Why This Beats a Toy Prompt Demo

A single prompt can look good in a meeting. A harness shows production behavior:

- The agent has to use shared context instead of guessing.
- Tools are constrained and auditable.
- Dangerous actions are blocked by hooks/sensors.
- Memory prevents repeated investigation.
- Review rules are executable, not just written in a policy document.
- The final scorecard is objective enough for management.

## Quick Start

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -e .
harness-demo run --scenario incident-response --lane raw-strong
harness-demo run --scenario incident-response --lane hand-built
harness-demo run --scenario incident-response --lane strands-sdk
harness-demo compare --scenario incident-response
```

The current implementation includes an offline deterministic demo runner. That means the management walkthrough works even before API keys are configured.

## Live Model Setup

Ollama local or cloud-offload mode:

```bash
ollama signin
ollama pull gpt-oss:20b-cloud
ollama pull gpt-oss:120b-cloud
```

OpenAI-compatible mode for Ollama:

```bash
export OLLAMA_BASE_URL=http://localhost:11434/v1
export OLLAMA_API_KEY=ollama
export HARNESS_MODEL=gpt-oss:20b
export STRONG_MODEL=gpt-oss:120b
```

Ollama supports OpenAI-compatible `/v1/chat/completions`, including tools and JSON mode for supported models.

## Strands Fit

Strands is the SDK abstraction layer in the demo. It lets us show that the industry is packaging harness concepts into reusable agent runtimes:

- tools
- hooks
- context/conversation managers
- session managers
- memory stores
- observability
- guardrails and steering
- multi-agent patterns such as agent-as-tool and swarm-style coordination

See [docs/strands-fit.md](docs/strands-fit.md).

## DeepSeek Fit

DeepSeek is the plug-and-play provider harness lane once the exact package/release is verified. The demo treats this as a provider-specific adapter that hides model/provider quirks behind a simple interface.

See [docs/deepseek-provider-harness.md](docs/deepseek-provider-harness.md).

## Repository Structure

```text
cases/incident-response/      Primary multi-agent demo scenario
docs/                         Management story, architecture, SDK/provider notes
src/harness_demo/             CLI, runners, scenario loading, scoring
tests/                        Focused tests for score and scenario behavior
reports/                      Generated demo scorecards
```

## Sources

- Martin Fowler: Harness engineering for coding agent users, 02 April 2026: https://martinfowler.com/articles/harness-engineering.html
- Strands Agents: https://strandsagents.com/
- Ollama OpenAI compatibility: https://docs.ollama.com/api/openai-compatibility
- Ollama Cloud docs: https://docs.ollama.com/cloud
