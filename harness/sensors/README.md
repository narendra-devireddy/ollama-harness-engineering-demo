# Sensors

Sensors are deterministic or inferential checks that help the model self-correct before a human reviews the result.

Initial deterministic sensors:
- JSON parse check.
- Pydantic schema validation.
- Approved fixture comparison.
- Numeric consistency checks for totals and line items.

Possible later inferential sensors:
- Judge whether unknown fields were honestly left as `null` instead of invented.
- Judge whether vendor names were normalized consistently.
