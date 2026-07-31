# Cost estimation

TokenPilot estimates text-token cost with:

```text
(input_tokens × input_price + output_tokens × output_price) / 1,000,000
```

The catalog includes standard short-context prices published on 2026-07-30. Costs vary with the selected service tier, long-context pricing, cache writes/reads, regional processing, tools, output length, and future provider changes. Treat the estimate as a guardrail, not an invoice.

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
- Observe `tokenpilot_estimated_cost_usd_total` and `tokenpilot_actual_cost_usd_total`.
- Measure quality, latency, total token use, and cost together; lower spend is not a success if quality declines.
