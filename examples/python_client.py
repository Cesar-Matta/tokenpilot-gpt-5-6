"""Minimal TokenPilot client using only the Python standard library."""

from __future__ import annotations

import json
import os
import urllib.request

payload = {
    "input": "Extract the order number and return concise JSON.",
    "signals": {"task_type": "extraction", "domain": "general"},
    "max_cost_usd": 0.02,
}
request = urllib.request.Request(
    f"{os.environ['TOKENPILOT_URL'].rstrip('/')}/v1/responses",
    data=json.dumps(payload).encode(),
    headers={
        "Content-Type": "application/json",
        "X-TokenPilot-Key": os.environ["TOKENPILOT_API_KEY"],
    },
    method="POST",
)
with urllib.request.urlopen(request, timeout=90) as response:
    print(json.dumps(json.load(response), indent=2))
