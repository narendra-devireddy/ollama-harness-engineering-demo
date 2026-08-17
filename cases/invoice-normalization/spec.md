# Invoice Normalization Case

Convert invoice-like text into structured JSON for downstream accounting automation.

The harnessed lane receives this spec, the schema, examples, and validation feedback. The weak-harness lane receives only the short prompt in `prompts/bare.md`.

## Success Criteria

- Valid JSON.
- Valid schema.
- Exact match against approved fixtures for deterministic fields.
- No invented data.
- Totals are internally consistent.
