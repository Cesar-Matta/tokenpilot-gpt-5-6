"""Run deterministic routing policy regression cases without OpenAI API calls."""

from __future__ import annotations

from pathlib import Path

import yaml

from app.config import Settings
from app.models import RouteRequest
from app.routing import decide_route


def main() -> int:
    path = Path(__file__).resolve().parents[1] / "evals" / "routing_cases.yaml"
    suite = yaml.safe_load(path.read_text(encoding="utf-8"))
    failures: list[str] = []
    for case in suite["cases"]:
        actual = decide_route(RouteRequest.model_validate(case["request"]), Settings())
        if actual.selected_tier.value != case["expected_tier"]:
            failures.append(
                f"{case['name']}: expected {case['expected_tier']}, "
                f"got {actual.selected_tier.value}"
            )
    if failures:
        print("\n".join(failures))
        return 1
    print(f"Routing evals passed: {len(suite['cases'])}/{len(suite['cases'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
