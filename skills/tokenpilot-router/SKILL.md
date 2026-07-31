---
name: tokenpilot-router
description: Design, configure, review, or operate a cost-aware OpenAI GPT-5.6 router using Luna by default and Terra or Sol for greater complexity, risk, uncertainty, context, or domain requirements. Use when creating model-routing policies, reviewing cost controls, integrating TokenPilot, calibrating model tiers, or investigating unexpected routing behavior.
---

# TokenPilot Router

Use this skill to make routing decisions explainable, conservative, and measurable.

## Execution boundary

The skill operates as an advisory policy layer unless the caller explicitly
provides a running TokenPilot API Server:

- Standalone operation requires no OpenAI API key or server process.
- Do not read `.env` or transmit prompts to an external service in standalone mode.
- Return a routing recommendation; do not claim to change the model assigned to
  the current host session.
- Use server endpoints only when the caller explicitly requests API integration
  or execution.

## Workflow

1. Read the caller's task, domain, correctness risk, latency target, context size, and budget.
2. Keep `gpt-5.6-luna` as the default for routine volume work.
3. Raise to `gpt-5.6-terra` for moderate complexity, technical nuance, large context, or low upstream confidence.
4. Raise to `gpt-5.6-sol` for critical risk, difficult reasoning, safety-sensitive work, or an evaluation-proven quality need.
5. Enforce a domain floor. Never let an explicit cost preference reduce a protected domain below its approved minimum.
6. Return the tier, model ID, `reasoning.effort`, signals, reasons, estimated cost, fallback path, and policy version.
7. Validate routing changes against representative tasks. Compare task success, required evidence, latency, total tokens, and cost together.

## Guardrails

- Do not use an additional model only to classify routine requests unless evaluation data proves its benefit exceeds its cost.
- Do not claim that a confidence signal proves factual correctness; use task-specific validation for that.
- Do not silently downgrade high-risk work because of a budget cap. Reject or require an explicit human decision.
- Escalate only after connection failures or provider `5xx` responses, and recheck the budget first. Do not escalate `429`, authentication, validation, safety, or irreversible action failures.
- Keep API keys and raw sensitive prompts out of configuration, logs, examples, and evaluation fixtures.

## Optional server integration

For TokenPilot's default policy, read [references/default-policy.md](references/default-policy.md). For implementation, use:

- `POST /v1/route` to inspect a decision without provider spend.
- `POST /v1/responses` to execute through the Responses API.
- `config/policy.yaml` for thresholds and domain floors.
- `config/models.yaml` for model IDs and dated cost inputs.

When server files or endpoints are unavailable, apply the bundled default
policy and remain in standalone mode.

## Output format

Return this compact structure when asked to recommend a route:

```text
Tier: luna | terra | sol
Model: gpt-5.6-...
Reasoning: low | medium | high
Reasons: [specific signals]
Fallback: [only higher eligible tiers]
Cost: [dated estimate and assumptions]
Validation: [how quality will be measured]
```
