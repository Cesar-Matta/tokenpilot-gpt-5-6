# Routing and fallback policies

## Signal model

TokenPilot computes a score from these signals:

| Signal | Range | Meaning |
|---|---:|---|
| Complexity | 0–100 | Number of constraints, requested reasoning, and input size |
| Risk | 0–100 | Consequence if the output is incomplete or wrong |
| Confidence | 0–1 | Confidence supplied by the caller or upstream evaluator; lower confidence adds escalation pressure |
| Context | tokens | Exact count supplied by the client, otherwise a visible character heuristic |
| Task type | enum | Extraction and classification are cheaper than analysis, code, or decision support |
| Domain | enum | Applies an immutable minimum model tier |

All thresholds are versioned in [`config/policy.yaml`](../config/policy.yaml). Treat its defaults as a starting hypothesis and calibrate them with representative evaluation data.

## Default routing table

| Condition | Route |
|---|---|
| Low score, general domain | Luna with `reasoning.effort=low` |
| Moderate score or low supplied confidence | Terra with `reasoning.effort=medium` |
| Risk ≥ 70 or high aggregate score | Sol with `reasoning.effort=high` |
| Legal, medical, financial, or security domain | At least Terra |
| Safety domain | Sol |

## Fallback behavior

1. A selected tier is called once.
2. A connection-level failure or `5xx` may escalate to the next configured tier.
3. A `429` never escalates to a costlier model because the limit commonly applies across models.
4. Escalation moves up at most two tiers and never down.
5. Every candidate tier is costed and checked against the per-request budget before its call.
6. Authentication, validation, safety refusal, rate-limit, and budget errors do not retry.
7. The API returns the chosen tier, all reasons, and the number of attempts.

A budget may downgrade an automatically selected general-domain tier to Luna. It never overrides an explicit `force_model` or a domain minimum; execution rejects those requests when their estimate exceeds the cap.

Use application-level quality gates for semantic checks such as required fields, citations, source coverage, or domain review. Configure these upstream or extend `OpenAIExecutor` with a task-specific validator; do not pretend a generic confidence score proves correctness.

## Reasoning settings

TokenPilot uses `low`, `medium`, and `high` as tier defaults. Callers can set any supported GPT-5.6 `reasoning.effort` value explicitly. Reserve `xhigh` and `max` for measured, quality-first workloads, and compare them against lower settings on representative tasks. OpenAI recommends the Responses API for reasoning, tool-calling, and multi-turn workflows. [Official model guidance](https://developers.openai.com/api/docs/guides/latest-model?model=gpt-5.6)
