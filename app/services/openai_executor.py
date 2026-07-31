"""Responses API execution with bounded escalation for transient provider failures."""

from __future__ import annotations

from typing import Any

from openai import APIError, AsyncOpenAI

from app.catalog import ModelCatalog, get_catalog
from app.config import Settings
from app.models import ExecuteResponse, ModelTier, RouteDecision, RouteRequest
from app.routing import decide_route


class BudgetExceededError(ValueError):
    """Raised before a provider call when the request cannot meet its budget cap."""


class OpenAIExecutor:
    def __init__(
        self, settings: Settings, client: Any | None = None, catalog: ModelCatalog | None = None
    ) -> None:
        self.settings = settings
        self.catalog = catalog or get_catalog()
        self.client = client

    def _client(self) -> AsyncOpenAI:
        if not self.settings.openai_api_key:
            raise RuntimeError("OPENAI_API_KEY is not configured")
        return self.client or AsyncOpenAI(
            api_key=self.settings.openai_api_key,
            timeout=self.settings.request_timeout_seconds,
        )

    async def execute(self, request: RouteRequest) -> ExecuteResponse:
        decision = decide_route(request, self.settings, self.catalog)
        if (
            request.max_cost_usd is not None
            and decision.estimated_cost.estimated_usd > request.max_cost_usd
        ):
            raise BudgetExceededError("Estimated request cost exceeds max_cost_usd")
        tiers = [decision.selected_tier, *decision.escalation_path]
        last_error: Exception | None = None
        for attempts, tier in enumerate(tiers, start=1):
            attempt_decision = (
                decision
                if tier == decision.selected_tier
                else self._decision_for_tier(decision, tier)
            )
            try:
                response = await self._client().responses.create(
                    model=attempt_decision.selected_model,
                    input=request.input,
                    instructions=request.instructions,
                    reasoning={"effort": attempt_decision.reasoning_effort},
                    text={"verbosity": request.text_verbosity},
                    safety_identifier=request.safety_identifier,
                    metadata=request.metadata or None,
                )
                payload = response.model_dump(mode="json")
                return ExecuteResponse(
                    decision=attempt_decision,
                    response=payload,
                    attempts=attempts,
                    actual_cost_usd=self._actual_cost(payload, tier),
                )
            except APIError as error:
                last_error = error
                if not self._is_transient(error) or tier == tiers[-1]:
                    raise
        raise RuntimeError("Execution failed without a provider error") from last_error

    def _decision_for_tier(self, decision: RouteDecision, tier: ModelTier) -> RouteDecision:
        return decision.model_copy(
            update={
                "selected_tier": tier,
                "selected_model": self.catalog.model_id(tier),
                "reasoning_effort": "medium" if tier is ModelTier.TERRA else "high",
                "reasons": [
                    *decision.reasons,
                    f"Escalated after a transient provider failure to {tier.value}.",
                ],
            }
        )

    @staticmethod
    def _is_transient(error: APIError) -> bool:
        status_code = getattr(error, "status_code", None)
        return status_code is None or status_code == 429 or status_code >= 500

    def _actual_cost(self, payload: dict[str, Any], tier: ModelTier) -> float | None:
        usage = payload.get("usage") or {}
        input_tokens = usage.get("input_tokens")
        output_tokens = usage.get("output_tokens")
        if not isinstance(input_tokens, int) or not isinstance(output_tokens, int):
            return None
        return self.catalog.estimate(tier, input_tokens, output_tokens).estimated_usd
