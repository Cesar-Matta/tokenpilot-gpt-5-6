from app.config import Settings
from app.models import Domain, ModelTier, RouteRequest, RoutingSignals, TaskType
from app.routing import decide_route


def test_simple_request_uses_luna() -> None:
    decision = decide_route(RouteRequest(input="Summarize this short note."), Settings())

    assert decision.selected_tier is ModelTier.LUNA
    assert decision.selected_model == "gpt-5.6-luna"
    assert decision.reasoning_effort == "low"


def test_safety_domain_enforces_sol() -> None:
    decision = decide_route(
        RouteRequest(input="Classify this report.", signals=RoutingSignals(domain=Domain.SAFETY)),
        Settings(),
    )

    assert decision.selected_tier is ModelTier.SOL
    assert any("Domain policy" in reason for reason in decision.reasons)


def test_low_confidence_escalates_to_terra() -> None:
    decision = decide_route(
        RouteRequest(
            input="What should we do?",
            signals=RoutingSignals(confidence=0.2, task_type=TaskType.QUESTION_ANSWERING),
        ),
        Settings(),
    )

    assert decision.selected_tier is ModelTier.TERRA
    assert decision.signal_scores["confidence_penalty"] > 0


def test_force_model_cannot_bypass_domain_floor() -> None:
    decision = decide_route(
        RouteRequest(
            input="Review this contract.",
            signals=RoutingSignals(domain=Domain.LEGAL, force_model=ModelTier.LUNA),
        ),
        Settings(),
    )

    assert decision.selected_tier is ModelTier.TERRA


def test_max_cost_can_choose_luna_when_policy_allows() -> None:
    decision = decide_route(
        RouteRequest(
            input="Explain this concept with a detailed answer.",
            signals=RoutingSignals(complexity=50),
            max_cost_usd=0.000001,
        ),
        Settings(),
    )

    assert decision.selected_tier is ModelTier.LUNA
    assert decision.reasoning_effort == "low"


def test_long_context_estimate_uses_long_pricing() -> None:
    decision = decide_route(
        RouteRequest(
            input="Analyze this document.",
            signals=RoutingSignals(context_tokens=2_000),
        ),
        Settings(long_context_token_threshold=1_000),
    )

    assert decision.estimated_cost.context_band == "long"


def test_budget_does_not_silently_override_forced_model() -> None:
    decision = decide_route(
        RouteRequest(
            input="Use the requested model.",
            signals=RoutingSignals(force_model=ModelTier.SOL),
            max_cost_usd=0.001,
        ),
        Settings(),
    )

    assert decision.selected_tier is ModelTier.SOL
    assert decision.estimated_cost.estimated_usd > 0.001
    assert "execution will be rejected" in decision.reasons[-1]
