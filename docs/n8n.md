# Workflow automation integration

TokenPilot works with any platform that can make an HTTP request. This generic example uses a workflow HTTP Request node.

## Configure a route-only request

- Method: `POST`
- URL: `https://YOUR_TOKENPILOT_HOST/v1/route`
- Authentication: header auth
- Header name: `X-TokenPilot-Key`
- Header value: your router key
- Content type: JSON

```json
{
  "input": "{{ $json.text }}",
  "signals": {
    "task_type": "summarization",
    "domain": "general",
    "confidence": 0.9
  },
  "max_cost_usd": 0.02
}
```

Use the returned `selected_model`, `reasons`, and `estimated_cost` for auditing or a manual approval branch. Use `/v1/responses` when TokenPilot should execute the OpenAI request itself.

## Configure execution

```json
{
  "input": "{{ $json.text }}",
  "instructions": "Return a concise JSON object with summary and action_items.",
  "signals": {
    "task_type": "analysis",
    "domain": "general",
    "risk": 25
  },
  "allow_escalation": true,
  "max_escalations": 1
}
```

Do not put the OpenAI API key in the workflow. Store only the TokenPilot client key in the workflow credential store; the OpenAI key remains in TokenPilot's runtime secret manager.
