# Industry Spectrum: Harness Engineering Is Becoming Productized

This project demonstrates the harness pattern with a live hand-built incident-response workflow. The broader management point is that the industry is moving quickly from hand-built harnesses toward SDKs and plug-and-play harness runtimes.

## Spectrum

| Level | What it means | Demo stance |
| --- | --- | --- |
| No harness | Single model call, no operational controls | Live baseline in Colab |
| Weak harness | Multi-agent/shared memory exists, but memory is ungoverned and feedback loops are absent | Live weak-harness lane |
| Strong hand-built harness | Guides, controlled tools, governed memory, sensors, reviewer, repair | Live hand-built lane |
| SDK harness | Framework packages common harness capabilities | Strands section in notebook |
| Plug-and-play harness runtime | Provider/runtime packages models, tools, sessions, sandboxes, storage, loops, scheduling, UI | DeepSeek Harness section in notebook |

## Strands Agents

Strands Agents presents itself as an open-source toolkit for building production agents with Python and TypeScript SDKs. Its public site emphasizes tools, hooks, context management, execution limits, observability, guardrails, steering, and multi-agent patterns.

How to position it:

> Strands shows that the harness ideas we hand-built are becoming SDK abstractions: tools, hooks, conversation/session memory, observability, and steering.

Source: https://strandsagents.com/

## DeepSeek Harness

DeepSeek Harness (`dsh`) is in developer preview and open source. Its public positioning is “Everything is a plugin”: models, tools, skills, sessions, sandboxes, storage, loops, scheduling, and UI are all plugin-composable. It also emphasizes traceable runs through append-only session logs.

How to position it:

> DeepSeek Harness shows the plug-and-play direction: harness capabilities are becoming runtime infrastructure, not just application code.

Source: https://deepseek.com/harness/en/

## Demo Boundary

Do not claim Strands or DeepSeek results unless they are wired into live execution. In this version:

- Live proof: Ollama Cloud through our no/weak/strong harness lanes.
- Industry acceleration: Strands and DeepSeek Harness as source-backed examples of the ecosystem productizing harness concepts.
