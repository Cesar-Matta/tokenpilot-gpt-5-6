# API reference

The generated contract is available at `/openapi.json`; Swagger UI is at `/docs`.

## Authentication

Set `REQUIRE_API_KEY=true` and configure `TOKENPILOT_API_KEYS` before exposing the service. Send one configured key in:

```http
X-TokenPilot-Key: your-router-key
```

The service refuses to start in `ENVIRONMENT=production` when API-key protection is disabled.

## `POST /v1/route`

Return a route decision without calling OpenAI.

```json
{
  "input": "Assess the risk in this proposal.",
  "signals": {
    "complexity": 70,
    "risk": 65,
    "confidence": 0.55,
    "context_tokens": 8000,
    "domain": "general",
    "task_type": "analysis"
  },
  "max_cost_usd": 0.10,
  "allow_escalation": true,
  "max_escalations": 1
}
```

The response includes `selected_model`, `reasoning_effort`, `signal_scores`, `reasons`, an escalation path, and a cost estimate.

## `POST /v1/responses`

Use the same body as `/v1/route`. TokenPilot forwards `input`, optional `instructions`, `reasoning.effort`, `text.verbosity`, `metadata`, and an optional privacy-preserving `safety_identifier` to the Responses API.

`OPENAI_API_KEY` is required. The returned payload contains the provider response as an object, never a hidden transformation of the response.

## `POST /v1/estimate`

```json
{
  "tier": "terra",
  "input_tokens": 12000,
  "output_tokens": 800
}
```

Use this endpoint for preflight budgets only. Pricing is configuration data, not a billing record.

## Errors

All handled errors use:

```json
{
  "error": {
    "code": "HTTP_401",
    "message": "Invalid API key.",
    "request_id": "..."
  }
}
```

Save `X-Request-ID` when reporting an issue. Do not send prompts or keys in an issue.
