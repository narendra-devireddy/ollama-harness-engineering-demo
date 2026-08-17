# Prior Similar Incident

On 2026-07-29, checkout latency rose during a flash sale because promotion price cache misses caused duplicate database lookups. The safest fix was enabling the single-flight lock and lowering TTL during rollout. Restarting checkout pods did not help and temporarily worsened the cache miss burst.
