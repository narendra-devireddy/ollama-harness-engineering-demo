# Architecture

```mermaid
flowchart LR
    Incident[Incident ticket] --> Lane{Demo lane}
    Lane --> Raw[Raw strong model]
    Lane --> Built[Hand-built harness]
    Lane --> Strands[Strands SDK harness]
    Lane --> Provider[DeepSeek provider harness]

    Built --> Memory[Shared incident memory]
    Built --> Tools[Controlled tools]
    Built --> Sensors[Validation sensors]
    Built --> Review[Reviewer gate]

    Strands --> STools[Strands tools]
    Strands --> SHooks[Hooks and steering]
    Strands --> SMemory[Conversation/session memory]
    Strands --> SOtel[Observability]

    Provider --> PAdapter[Provider adapter]
    PAdapter --> PControls[Reasoning/tool protocol controls]

    Raw --> Score[Scorecard]
    Built --> Score
    Strands --> Score
    Provider --> Score
```

## Harness Components

| Component | Hand-built implementation | Strands abstraction | Provider harness abstraction |
| --- | --- | --- | --- |
| Workflow | Python runner | Agent runtime / multi-agent patterns | Provider adapter |
| Context | Explicit incident memory object | Conversation/session managers | Provider-managed context rules |
| Tools | Python functions | `@tool` and tool registry | Provider-compatible tools |
| Sensors | Custom checks | Hooks, plugins, steering | Protocol validation |
| Repair | Retry loop | Agent feedback through hooks | Provider-specific retries |
| Observability | JSON reports | OpenTelemetry hooks/integrations | CLI/probe reports |

## Why The Demo Has Four Lanes

The spectrum matters:

- Hand-built proves what the harness does.
- Strands proves the industry is abstracting the harness into SDKs.
- DeepSeek provider harness proves some controls can become plug-and-play.
- Raw model proves why model quality alone is insufficient.
