"""Deterministic, explainable model selection. No model call is used to route a request."""

from __future__ import annotations

import json
from pathlib import Path

import yaml

from app.catalog import ModelCatalog, get_catalog
from app.config import Settings
from app.models import Domain, ModelTier, RouteDecision, RouteRequest, RoutingSignals

TIER_ORDER = (ModelTier.LUNA, ModelTier.TERRA, ModelTier.SOL)


class RoutingPolicy:
    def __init__(self, data: dict) -> None:
        self.version = data["version"]
        self.thresholds = data["thresholds"]
        self.domain_minimums = {
            Domain(domain): ModelTier(tier) for domain, tier in data["domain_minimums"].items()
        }
        self.task_weights = data["task_weights"]


def get_policy() -> RoutingPolicy:
    path = Path(__file__).resolve().parents[1] / "config" / "policy.yaml"
    return RoutingPolicy(yaml.safe_load(path.read_text(encoding="utf-8")))


def _input_text(request: RouteRequest) -> str:
    if isinstance(request.input, str):
        return request.input
    return json.dumps(request.input, ensure_ascii=False)


def estimate_input_tokens(request: RouteRequest) -> int:
    """Use a conservative character heuristic; clients can supply an exact count."""
    if request.signals.context_tokens is not None:
        return request.signals.context_tokens
    return max(1, len(_input_text(request)) // 4 + len(request.instructions or "") // 4)


def _minimum_tier(signals: RoutingSignals, policy: RoutingPolicy) -> ModelTier:
    return policy.domain_minimums.get(signals.domain, ModelTier.LUNA)


def _at_least(current: ModelTier, minimum: ModelTier) -> ModelTier:
    return TIER_ORDER[max(TIER_ORDER.index(current), TIER_ORDER.index(minimum))]


def _next_tiers(tier: ModelTier, max_escalations: int) -> list[ModelTier]:
    start = TIER_ORDER.index(tier) + 1
    return list(TIER_ORDER[start : start + max_escalations])


def decide_route(
    request: RouteRequest,
    settings: Settings,
    catalog: ModelCatalog | None = None,
    policy: RoutingPolicy | None = None,
) -> RouteDecision:
    """Select a model using explicit signals, conservative domain floors, and budget limits."""
    catalog = catalog or get_catalog()
    policy = policy or get_policy()
    signals = request.signals
    input_tokens = estimate_input_tokens(request)
    complexity = (
        signals.complexity
        if signals.complexity is not None
        else min(100, len(_input_text(request)) // 80)
    )
    risk = signals.risk if signals.risk is not None else 0
    confidence = signals.confidence if signals.confidence is not None else 1.0
    task_score = float(policy.task_weights.get(signals.task_type.value, 10))
    context_score = (
        float(policy.thresholds["long_context_score"])
        if input_tokens >= settings.long_context_token_threshold
        else 0.0
    )
    confidence_score = (
        (1.0 - confidence) * 50 if confidence < policy.thresholds["low_confidence"] else 0.0
    )
    total = min(
        100.0, complexity * 0.45 + risk * 0.35 + task_score + context_score + confidence_score
    )
    reasons: list[str] = []
    if risk >= 70:
        tier = ModelTier.SOL
        reasons.append("Risk score is at least 70; critical-work policy selected Sol.")
    elif total >= float(policy.thresholds["sol_score"]):
        tier = ModelTier.SOL
        reasons.append("Combined routing score reached the Sol threshold.")
    elif total >= float(policy.thresholds["terra_score"]):
        tier = ModelTier.TERRA
        reasons.append("Combined routing score reached the Terra threshold.")
    else:
        tier = ModelTier.LUNA
        reasons.append("Request fits the efficient default route.")

    minimum = _minimum_tier(signals, policy)
    if tier != _at_least(tier, minimum):
        tier = _at_least(tier, minimum)
        reasons.append(f"Domain policy enforces a minimum tier of {minimum.value}.")
    if signals.force_model is not None:
        forced = _at_least(signals.force_model, minimum)
        tier = forced
        reasons.append(f"Caller requested {signals.force_model.value}; domain floor was preserved.")

    output_tokens = _estimate_output_tokens(request, input_tokens)
    long_context = input_tokens >= settings.long_context_token_threshold
    estimate = catalog.estimate(tier, input_tokens, output_tokens, long_context=long_context)
    limit = (
        request.max_cost_usd
        if request.max_cost_usd is not None
        else settings.default_request_budget_usd
    )
    if limit is not None and estimate.estimated_usd > limit:
        cheapest = catalog.estimate(
            ModelTier.LUNA, input_tokens, output_tokens, long_context=long_context
        )
        if (
            minimum is ModelTier.LUNA
            and signals.force_model is None
            and cheapest.estimated_usd <= limit
        ):
            tier = ModelTier.LUNA
            estimate = cheapest
            reasons.append("Budget cap selected the lowest compliant tier.")
        else:
            reasons.append("Estimated cost exceeds the supplied cap; execution will be rejected.")

    effort = request.reasoning_effort or _default_effort(tier)
    return RouteDecision(
        selected_tier=tier,
        selected_model=catalog.model_id(tier),
        reasoning_effort=effort,
        escalation_path=_next_tiers(tier, request.max_escalations)
        if request.allow_escalation
        else [],
        signal_scores={
            "complexity": float(complexity),
            "risk": float(risk),
            "confidence_penalty": round(confidence_score, 2),
            "task": task_score,
            "context": context_score,
            "total": round(total, 2),
        },
        reasons=reasons,
        estimated_cost=estimate,
        policy_version=policy.version,
    )


def _estimate_output_tokens(request: RouteRequest, input_tokens: int) -> int:
    if request.signals.task_type.value in {"classification", "extraction"}:
        return min(500, max(100, input_tokens // 10))
    return min(4_000, max(500, input_tokens // 2))


def _default_effort(tier: ModelTier) -> str:
    return "low" if tier is ModelTier.LUNA else "medium" if tier is ModelTier.TERRA else "high"
