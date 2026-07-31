import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app
from app.services.openai_executor import OpenAIExecutor


def test_health_and_route_endpoints() -> None:
    application = create_app(Settings())
    with TestClient(application) as client:
        assert client.get("/health/live").json() == {"status": "ok"}
        response = client.post("/v1/route", json={"input": "Extract the invoice number."})

    assert response.status_code == 200
    assert response.json()["selected_model"] == "gpt-5.6-luna"
    assert response.headers["X-Request-ID"]


def test_api_key_protection() -> None:
    application = create_app(Settings(require_api_key=True, tokenpilot_api_keys="secret-one"))
    with TestClient(application) as client:
        denied = client.post("/v1/route", json={"input": "hello"})
        allowed = client.post(
            "/v1/route", json={"input": "hello"}, headers={"X-TokenPilot-Key": "secret-one"}
        )

    assert denied.status_code == 401
    assert allowed.status_code == 200


def test_metrics_use_auth_and_do_not_label_arbitrary_paths() -> None:
    application = create_app(Settings(require_api_key=True, tokenpilot_api_keys="secret-one"))
    unique_path = "/private-user-path-cardinality-test"
    with TestClient(application) as client:
        client.get(unique_path)
        denied = client.get("/metrics")
        allowed = client.get("/metrics", headers={"X-TokenPilot-Key": "secret-one"})

    assert denied.status_code == 401
    assert allowed.status_code == 200
    assert unique_path not in allowed.text
    assert 'endpoint="unmatched"' in allowed.text


def test_readiness_can_require_openai_execution() -> None:
    application = create_app(Settings(require_openai_for_readiness=True))
    with TestClient(application) as client:
        response = client.get("/health/ready")

    assert response.status_code == 503
    assert response.json()["mode"] == "routing_only"


def test_rate_limit_is_enforced() -> None:
    application = create_app(Settings(request_rate_limit_per_minute=1))
    with TestClient(application) as client:
        assert client.post("/v1/route", json={"input": "first"}).status_code == 200
        limited = client.post("/v1/route", json={"input": "second"})

    assert limited.status_code == 429


def test_production_requires_api_key_protection() -> None:
    application = create_app(Settings(environment="production", require_api_key=False))

    with pytest.raises(RuntimeError, match="REQUIRE_API_KEY"), TestClient(application):
        pass


def test_production_requires_at_least_one_configured_key() -> None:
    application = create_app(Settings(environment="production", require_api_key=True))

    with pytest.raises(RuntimeError, match="TOKENPILOT_API_KEYS"), TestClient(application):
        pass


class FakeResponse:
    def model_dump(self, mode: str) -> dict:
        assert mode == "json"
        return {
            "id": "resp_test",
            "status": "completed",
            "usage": {"input_tokens": 10, "output_tokens": 20},
        }


class FakeResponses:
    async def create(self, **kwargs):
        assert kwargs["model"] == "gpt-5.6-luna"
        return FakeResponse()


class FakeOpenAI:
    responses = FakeResponses()


def test_responses_endpoint_uses_injected_client() -> None:
    settings = Settings(openai_api_key="not-a-real-key")
    application = create_app(settings, executor=OpenAIExecutor(settings, client=FakeOpenAI()))
    with TestClient(application) as client:
        response = client.post("/v1/responses", json={"input": "Extract the order number."})

    assert response.status_code == 200
    assert response.json()["response"]["id"] == "resp_test"
    assert response.json()["actual_cost_usd"] > 0
