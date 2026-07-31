# Routing evaluations

Routing thresholds are product hypotheses, not universal truths. The repository includes a deterministic regression suite in [`evals/routing_cases.yaml`](../evals/routing_cases.yaml) so policy changes cannot silently alter known routing expectations.

Run it without an OpenAI key:

```bash
python scripts/run_routing_evals.py
```

The public sample covers economical defaults, low confidence, difficult code, domain floors, and forced-tier protection. Before production use:

1. Add anonymized cases representative of the deployment's real task mix.
2. Define expected quality, latency, cost, and escalation-rate targets.
3. Evaluate model outputs separately with task-specific rubrics and human review for high-risk domains.
4. Change one policy dimension at a time and compare against a fixed baseline.
5. Keep sensitive prompts and personal data out of public fixtures.

The deterministic suite validates routing behavior only. It does not prove model-answer quality, factual correctness, or domain suitability.
