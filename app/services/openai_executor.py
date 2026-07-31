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
        tiers = [decision.selected_tier, *decision.escalation_path]
        last_error: Exception | None = None
        for attempts, tier in enumerate(tiers, start=1):
            attempt_decision = (
                decision
                if tier == decision.selected_tier
                else self._decision_for_tier(decision, tier, request)
            )
            self._enforce_budget(attempt_decision, request)
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
                if not self._can_escalate(error) or tier == tiers[-1]:
                    raise
        raise RuntimeError("Execution failed without a provider error") from last_error

    def _decision_for_tier(
        self, decision: RouteDecision, tier: ModelTier, request: RouteRequest
    ) -> RouteDecision:
        estimate = self.catalog.estimate(
            tier,
            decision.estimated_cost.input_tokens,
            decision.estimated_cost.output_tokens,
            long_context=decision.estimated_cost.context_band == "long",
        )
        return decision.model_copy(
            update={
                "selected_tier": tier,
                "selected_model": self.catalog.model_id(tier),
                "reasoning_effort": request.reasoning_effort
                or ("medium" if tier is ModelTier.TERRA else "high"),
                "estimated_cost": estimate,
                "reasons": [
                    *decision.reasons,
                    f"Escalated after a transient provider failure to {tier.value}.",
                ],
            }
        )

    def _enforce_budget(self, decision: RouteDecision, request: RouteRequest) -> None:
        limit = (
            request.max_cost_usd
            if request.max_cost_usd is not None
            else self.settings.default_request_budget_usd
        )
        if limit is not None and decision.estimated_cost.estimated_usd > limit:
            raise BudgetExceededError(
                f"Estimated {decision.selected_tier.value} request cost "
                f"(${decision.estimated_cost.estimated_usd:.8f}) exceeds the "
                f"per-request cap (${limit:.8f})"
            )

    @staticmethod
    def _can_escalate(error: APIError) -> bool:
        status_code = getattr(error, "status_code", None)
        # A 429 commonly applies across models, so a costlier model is not a safe retry strategy.
        return status_code is None or status_code >= 500

    def _actual_cost(self, payload: dict[str, Any], tier: ModelTier) -> float | None:
        usage = payload.get("usage") or {}
        input_tokens = usage.get("input_tokens")
        output_tokens = usage.get("output_tokens")
        if not isinstance(input_tokens, int) or not isinstance(output_tokens, int):
            return None
        details = usage.get("input_tokens_details") or {}
        cached_tokens = details.get("cached_tokens", 0)
        cache_write_tokens = details.get("cache_write_tokens", 0)
        return self.catalog.estimate(
            tier,
            input_tokens,
            output_tokens,
            cached_input_tokens=cached_tokens if isinstance(cached_tokens, int) else 0,
            cache_write_tokens=cache_write_tokens if isinstance(cache_write_tokens, int) else 0,
            long_context=input_tokens >= self.settings.long_context_token_threshold,
        ).estimated_usd
