import httpx
import pytest
from openai import APIConnectionError, APIStatusError

from app.config import Settings
from app.models import ModelTier, RouteRequest
from app.services.openai_executor import BudgetExceededError, OpenAIExecutor


class FakeResponse:
    def model_dump(self, mode: str) -> dict:
        assert mode == "json"
        return {
            "id": "resp_test",
            "status": "completed",
            "usage": {
                "input_tokens": 1_000,
                "output_tokens": 500,
                "input_tokens_details": {"cached_tokens": 500, "cache_write_tokens": 0},
            },
        }


class SequenceResponses:
    def __init__(self, outcomes: list[object]) -> None:
        self.outcomes = outcomes
        self.models: list[str] = []

    async def create(self, **kwargs):
        self.models.append(kwargs["model"])
        outcome = self.outcomes.pop(0)
        if isinstance(outcome, Exception):
            raise outcome
        return outcome


class FakeOpenAI:
    def __init__(self, responses: SequenceResponses) -> None:
        self.responses = responses


def connection_error() -> APIConnectionError:
    return APIConnectionError(request=httpx.Request("POST", "https://api.openai.com/v1/responses"))


@pytest.mark.asyncio
async def test_escalation_recomputes_cost_for_new_tier() -> None:
    responses = SequenceResponses([connection_error(), FakeResponse()])
    executor = OpenAIExecutor(Settings(openai_api_key="test"), client=FakeOpenAI(responses))

    result = await executor.execute(RouteRequest(input="Routine request"))

    assert result.decision.selected_tier is ModelTier.TERRA
    assert result.decision.estimated_cost.estimated_usd > 0.001
    assert responses.models == ["gpt-5.6-luna", "gpt-5.6-terra"]


@pytest.mark.asyncio
async def test_budget_is_checked_before_every_escalation_attempt() -> None:
    responses = SequenceResponses([connection_error(), FakeResponse()])
    executor = OpenAIExecutor(Settings(openai_api_key="test"), client=FakeOpenAI(responses))

    with pytest.raises(BudgetExceededError, match="terra"):
        await executor.execute(RouteRequest(input="Routine request", max_cost_usd=0.001))

    assert responses.models == ["gpt-5.6-luna"]


@pytest.mark.asyncio
async def test_rate_limit_error_does_not_escalate_to_costlier_model() -> None:
    request = httpx.Request("POST", "https://api.openai.com/v1/responses")
    response = httpx.Response(429, request=request)
    error = APIStatusError("rate limited", response=response, body=None)
    responses = SequenceResponses([error, FakeResponse()])
    executor = OpenAIExecutor(Settings(openai_api_key="test"), client=FakeOpenAI(responses))

    with pytest.raises(APIStatusError):
        await executor.execute(RouteRequest(input="Routine request"))

    assert responses.models == ["gpt-5.6-luna"]
