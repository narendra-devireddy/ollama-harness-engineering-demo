# How Strands Fits

Strands is the SDK-level harness in this demo.

It is useful because it gives a Python and TypeScript agent runtime with production concepts already present: tools, hooks, context management, execution limits, observability, guardrails, integrations, memory stores, session managers, and multi-agent patterns.

## Mapping To Harness Engineering

| Harness concept | Strands concept |
| --- | --- |
| Feedforward guide | Agent system prompt, tools, selected context |
| Feedback sensor | Hook, plugin, steering handler |
| Controlled tool access | `@tool` functions and before-tool hooks |
| Shared context | Conversation manager / session manager |
| Long-term memory | Memory store integrations |
| Audit trail | OpenTelemetry and trace attributes |
| Multi-agent collaboration | Agent-as-tool, swarm-style orchestration, extensions |

## Demo Role

In the management demo, Strands is not the raw model. It is the packaged agent runtime.

The hand-built lane says: "Here are the controls."

The Strands lane says: "These controls are becoming standard SDK features."

## Example Shape

```python
from strands import Agent, tool
from strands.agent import SummarizingConversationManager
from strands.hooks import BeforeToolCallEvent, AfterToolCallEvent

@tool
def search_logs(query: str, hours: int = 6) -> list[dict]:
    return log_store.search(query=query, hours=hours)

def block_destructive_action(event: BeforeToolCallEvent):
    action = str(event.tool_use.get("input", {})).upper()
    if "DROP" in action or "DELETE" in action:
        event.cancel_tool = "Destructive operation blocked. Propose read-only investigation first."

agent = Agent(
    tools=[search_logs],
    hooks=[block_destructive_action],
    conversation_manager=SummarizingConversationManager(),
    trace_attributes={"service": "incident-response-demo"},
)

agent("Investigate the checkout latency incident and propose a safe next action.")
```

## Ollama Cloud

Ollama can be used through its OpenAI-compatible endpoint. In a live implementation, Strands can use an OpenAI-compatible model provider configuration, pointing the base URL at Ollama.
