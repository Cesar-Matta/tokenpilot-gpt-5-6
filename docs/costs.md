# Cost estimation

TokenPilot estimates standard-tier text-token cost with:

```text
(uncached_input × input_price
 + cached_input × cached_input_price
 + cache_write × cache_write_price
 + output × output_price) / 1,000,000
```

The catalog includes standard short- and long-context prices published on 2026-07-30. The configurable `LONG_CONTEXT_TOKEN_THRESHOLD` selects the pricing band. Regional processing, priority/flex/batch tiers, built-in tools, and future provider changes are not included. Treat the estimate as a guardrail, not an invoice.

## Example

For an estimated 10,000 input tokens and 1,000 output tokens:

| Tier | Estimated cost |
|---|---:|
| Luna | $0.0032 |
| Terra | $0.0320 |
| Sol | $0.0800 |

Luna is approximately 25× less expensive than Sol for this example, but it is not automatically appropriate for a high-risk task. Policy floors and evaluation results decide when the saving is safe.

## Operational recommendations

- Refresh `config/models.yaml` after checking the [official OpenAI pricing page](https://developers.openai.com/api/docs/pricing).
- Pass an exact `context_tokens` value from the caller when available.
- Set `max_cost_usd` per request for self-contained spending control.
- Optionally set `DEFAULT_REQUEST_BUDGET_USD`; it is checked before every provider attempt.
- Use a database or billing system for monthly/account-wide budgets. This stateless service does not claim to enforce them.
- Observe `tokenpilot_estimated_cost_usd_total` and `tokenpilot_actual_cost_usd_total`.
- Measure quality, latency, total token use, and cost together; lower spend is not a success if quality declines.
