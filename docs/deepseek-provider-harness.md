# DeepSeek Provider Harness Lane

This lane represents the most plug-and-play end of the spectrum.

The goal is to show that some harness responsibilities can be packaged by a provider-specific adapter:

- reasoning/thinking controls
- tool-call protocol handling
- streaming response aggregation
- token safety
- provider-specific retry behavior
- cache-aware prompt handling
- offline validation/probe commands

## Status

The exact DeepSeek harness package/release still needs verification before this lane is presented as a specific released dependency. The demo code keeps it as an adapter boundary so the real package can be swapped in later.

## Demo Message

Hand-built harness:

> We implement the controls ourselves.

Strands SDK:

> The agent SDK abstracts many controls.

DeepSeek provider harness:

> Provider-specific controls become plug-and-play.

## Adapter Shape

```python
class DeepSeekProviderHarness:
    def investigate(self, incident):
        # Real implementation will call the verified DeepSeek harness package.
        # The app only depends on this adapter contract.
        return response
```
