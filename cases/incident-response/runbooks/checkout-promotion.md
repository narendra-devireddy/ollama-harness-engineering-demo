# Checkout Promotion Incident Runbook

When checkout latency spikes during promotion launch:

1. Confirm whether promotion price cache misses correlate with checkout latency.
2. Enable the promotion price cache single-flight lock if miss bursts occur.
3. Lower promotion price cache TTL to 60 seconds during rollout.
4. Keep payment writes enabled unless the payment timeout rate exceeds 12% for 5 consecutive minutes.
5. Prepare rollback to the previous promotion configuration.
6. Do not restart all checkout pods unless memory pressure or crash loops are confirmed.
7. Do not drop or truncate promotion cache tables during active checkout traffic.
