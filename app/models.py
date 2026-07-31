"""Public API contracts for routing and execution."""

from __future__ import annotations

from enum import StrEnum
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ModelTier(StrEnum):
    LUNA = "luna"
    TERRA = "terra"
    SOL = "sol"


class Domain(StrEnum):
    GENERAL = "general"
    CUSTOMER_SUPPORT = "customer_support"
    CONTENT = "content"
    CODE = "code"
    DOCUMENT_ANALYSIS = "document_analysis"
    LEGAL = "legal"
    MEDICAL = "medical"
    FINANCIAL = "financial"
    SAFETY = "safety"
    SECURITY = "security"


class TaskType(StrEnum):
    GENERATION = "generation"
    CLASSIFICATION = "classification"
    EXTRACTION = "extraction"
    SUMMARIZATION = "summarization"
    QUESTION_ANSWERING = "question_answering"
    ANALYSIS = "analysis"
    CODE = "code"
    DECISION_SUPPORT = "decision_support"


class RoutingSignals(BaseModel):
    """Optional explicit signals; the router derives conservative defaults when omitted."""

    complexity: int | None = Field(default=None, ge=0, le=100)
    risk: int | None = Field(default=None, ge=0, le=100)
    confidence: float | None = Field(default=None, ge=0, le=1)
    context_tokens: int | None = Field(default=None, ge=0)
    domain: Domain = Domain.GENERAL
    task_type: TaskType = TaskType.GENERATION
    force_model: ModelTier | None = None


class RouteRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    input: str | list[dict[str, Any]] = Field(..., description="Responses API-compatible input.")
    instructions: str | None = Field(default=None, max_length=100_000)
    signals: RoutingSignals = Field(default_factory=RoutingSignals)
    max_cost_usd: float | None = Field(default=None, gt=0)
    allow_escalation: bool = True
    max_escalations: int = Field(default=1, ge=0, le=2)
    reasoning_effort: Literal["none", "low", "medium", "high", "xhigh", "max"] | None = None
    text_verbosity: Literal["low", "medium", "high"] = "medium"
    safety_identifier: str | None = Field(default=None, min_length=8, max_length=128)
    metadata: dict[str, str] = Field(default_factory=dict)

    @field_validator("input")
    @classmethod
    def require_non_empty_input(
        cls, value: str | list[dict[str, Any]]
    ) -> str | list[dict[str, Any]]:
        if isinstance(value, str) and not value.strip():
            raise ValueError("input must not be empty")
        if isinstance(value, list) and not value:
            raise ValueError("input must not be empty")
        return value


class CostEstimate(BaseModel):
    input_tokens: int = Field(ge=0)
    output_tokens: int = Field(ge=0)
    estimated_usd: float = Field(ge=0)
    pricing_version: str


class RouteDecision(BaseModel):
    selected_tier: ModelTier
    selected_model: str
    reasoning_effort: Literal["none", "low", "medium", "high", "xhigh", "max"]
    escalation_path: list[ModelTier]
    signal_scores: dict[str, float]
    reasons: list[str]
    estimated_cost: CostEstimate
    policy_version: str


class ExecuteResponse(BaseModel):
    decision: RouteDecision
    response: dict[str, Any]
    attempts: int = Field(ge=1)
    actual_cost_usd: float | None = Field(default=None, ge=0)


class ErrorBody(BaseModel):
    code: str
    message: str
    request_id: str | None = None


class ErrorResponse(BaseModel):
    error: ErrorBody


class EstimateRequest(BaseModel):
    input_tokens: int = Field(ge=0)
    output_tokens: int = Field(default=500, ge=0)
    tier: ModelTier = ModelTier.LUNA
