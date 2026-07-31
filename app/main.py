"""TokenPilot HTTP API."""

from __future__ import annotations

import time
import uuid
from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import Depends, FastAPI, Header, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from openai import APIError

from app.catalog import get_catalog
from app.config import Settings, get_settings
from app.models import (
    ErrorBody,
    ErrorResponse,
    EstimateRequest,
    ExecuteResponse,
    RouteDecision,
    RouteRequest,
)
from app.observability import (
    ACTUAL_COST,
    ESTIMATED_COST,
    LATENCY,
    REQUESTS,
    ROUTES,
    configure_logging,
    metrics_response,
)
from app.routing import decide_route
from app.security import SlidingWindowRateLimiter, authenticate
from app.services.openai_executor import BudgetExceededError, OpenAIExecutor


def create_app(settings: Settings | None = None, executor: OpenAIExecutor | None = None) -> FastAPI:
    settings = settings or get_settings()
    logger = configure_logging(settings.log_level)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        if settings.environment == "production" and not settings.require_api_key:
            raise RuntimeError("REQUIRE_API_KEY=true is required in production")
        app.state.settings = settings
        app.state.executor = executor or OpenAIExecutor(settings)
        app.state.limiter = SlidingWindowRateLimiter(settings.request_rate_limit_per_minute)
        yield

    app = FastAPI(
        title="TokenPilot GPT-5.6",
        summary="Smart model routing for OpenAI GPT-5.6 Luna, Terra, and Sol.",
        version="0.1.0",
        license_info={"name": "Apache-2.0", "url": "https://www.apache.org/licenses/LICENSE-2.0"},
        openapi_url="/openapi.json",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )
    if settings.cors_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=settings.cors_origins,
            allow_credentials=False,
            allow_methods=["POST", "GET"],
            allow_headers=["Content-Type", "X-TokenPilot-Key", "X-Request-ID"],
        )

    @app.middleware("http")
    async def request_context(request: Request, call_next):
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        request.state.request_id = request_id
        started = time.perf_counter()
        try:
            response = await call_next(request)
        except Exception:
            REQUESTS.labels(request.url.path, "500").inc()
            raise
        LATENCY.labels(request.url.path).observe(time.perf_counter() - started)
        REQUESTS.labels(request.url.path, str(response.status_code)).inc()
        logger.info(
            "request.completed",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "duration_ms": round((time.perf_counter() - started) * 1000, 2),
            },
        )
        response.headers["X-Request-ID"] = request_id
        return response

    @app.exception_handler(HTTPException)
    async def http_error(request: Request, error: HTTPException) -> JSONResponse:
        detail = error.detail if isinstance(error.detail, str) else "Request failed."
        return JSONResponse(
            status_code=error.status_code,
            content=ErrorResponse(
                error=ErrorBody(
                    code=f"HTTP_{error.status_code}",
                    message=detail,
                    request_id=request.state.request_id,
                )
            ).model_dump(),
            headers=error.headers,
        )

    @app.exception_handler(RequestValidationError)
    async def validation_error(request: Request, error: RequestValidationError) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=ErrorResponse(
                error=ErrorBody(
                    code="VALIDATION_ERROR",
                    message="Request validation failed.",
                    request_id=request.state.request_id,
                )
            ).model_dump(),
        )

    async def protected_client(
        request: Request,
        x_tokenpilot_key: Annotated[str | None, Header()] = None,
    ) -> str:
        client = authenticate(request, x_tokenpilot_key, settings)
        request.app.state.limiter.check(client)
        return client

    @app.get("/health/live", tags=["health"])
    async def liveness() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/health/ready", tags=["health"])
    async def readiness() -> dict[str, str]:
        return {"status": "ready", "environment": settings.environment}

    @app.get("/metrics", include_in_schema=False)
    async def metrics() -> JSONResponse:
        return metrics_response()

    @app.get("/v1/models", tags=["routing"])
    async def models(_: str = Depends(protected_client)) -> dict:
        catalog = get_catalog()
        return {"pricing_version": catalog.version, "models": catalog.public_models()}

    @app.post(
        "/v1/route",
        response_model=RouteDecision,
        responses={
            401: {"model": ErrorResponse},
            422: {"model": ErrorResponse},
            429: {"model": ErrorResponse},
        },
        tags=["routing"],
    )
    async def route(request: RouteRequest, _: str = Depends(protected_client)) -> RouteDecision:
        _check_size(request, settings)
        decision = decide_route(request, settings)
        ROUTES.labels(decision.selected_tier.value, request.signals.domain.value).inc()
        ESTIMATED_COST.labels(decision.selected_tier.value).inc(
            decision.estimated_cost.estimated_usd
        )
        return decision

    @app.post("/v1/estimate", tags=["routing"])
    async def estimate(request: EstimateRequest, _: str = Depends(protected_client)) -> dict:
        estimate_value = get_catalog().estimate(
            request.tier, request.input_tokens, request.output_tokens
        )
        return {
            "tier": request.tier,
            "model": get_catalog().model_id(request.tier),
            "estimate": estimate_value,
        }

    @app.post(
        "/v1/responses",
        response_model=ExecuteResponse,
        responses={
            400: {"model": ErrorResponse},
            401: {"model": ErrorResponse},
            502: {"model": ErrorResponse},
        },
        tags=["execution"],
    )
    async def responses(
        request: RouteRequest, _: str = Depends(protected_client)
    ) -> ExecuteResponse:
        _check_size(request, settings)
        try:
            result = await app.state.executor.execute(request)
        except BudgetExceededError as error:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)
            ) from error
        except RuntimeError as error:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(error)
            ) from error
        except APIError as error:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY, detail="OpenAI request failed."
            ) from error
        ROUTES.labels(result.decision.selected_tier.value, request.signals.domain.value).inc()
        ESTIMATED_COST.labels(result.decision.selected_tier.value).inc(
            result.decision.estimated_cost.estimated_usd
        )
        if result.actual_cost_usd is not None:
            ACTUAL_COST.labels(result.decision.selected_tier.value).inc(result.actual_cost_usd)
        return result

    return app


def _check_size(request: RouteRequest, settings: Settings) -> None:
    input_length = len(str(request.input)) + len(request.instructions or "")
    if input_length > settings.max_input_characters:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="Input exceeds configured size limit.",
        )


app = create_app()
