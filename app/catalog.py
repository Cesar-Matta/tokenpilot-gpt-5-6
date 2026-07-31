"""Versioned model catalog and cost calculations."""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import yaml

from app.models import CostEstimate, ModelTier


@dataclass(frozen=True)
class ContextPricing:
    input_per_million: float
    output_per_million: float
    cached_input_per_million: float
    cache_write_per_million: float


@dataclass(frozen=True)
class ModelPricing:
    model_id: str
    short: ContextPricing
    long: ContextPricing
    description: str


class ModelCatalog:
    def __init__(self, version: str, models: dict[ModelTier, ModelPricing]) -> None:
        self.version = version
        self.models = models

    def model_id(self, tier: ModelTier) -> str:
        return self.models[tier].model_id

    def estimate(
        self,
        tier: ModelTier,
        input_tokens: int,
        output_tokens: int,
        *,
        cached_input_tokens: int = 0,
        cache_write_tokens: int = 0,
        long_context: bool = False,
    ) -> CostEstimate:
        pricing = self.models[tier]
        rates = pricing.long if long_context else pricing.short
        cached_input_tokens = min(cached_input_tokens, input_tokens)
        cache_write_tokens = min(cache_write_tokens, input_tokens - cached_input_tokens)
        uncached_input_tokens = input_tokens - cached_input_tokens - cache_write_tokens
        amount = (
            uncached_input_tokens * rates.input_per_million
            + cached_input_tokens * rates.cached_input_per_million
            + cache_write_tokens * rates.cache_write_per_million
            + output_tokens * rates.output_per_million
        ) / 1_000_000
        return CostEstimate(
            input_tokens=input_tokens,
            cached_input_tokens=cached_input_tokens,
            cache_write_tokens=cache_write_tokens,
            output_tokens=output_tokens,
            estimated_usd=round(amount, 8),
            context_band="long" if long_context else "short",
            pricing_version=self.version,
        )

    def public_models(self) -> dict[str, dict]:
        return {
            tier.value: {
                "id": pricing.model_id,
                "short_context": pricing.short.__dict__,
                "long_context": pricing.long.__dict__,
                "description": pricing.description,
            }
            for tier, pricing in self.models.items()
        }


@lru_cache
def get_catalog() -> ModelCatalog:
    path = Path(__file__).resolve().parents[1] / "config" / "models.yaml"
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    models = {
        ModelTier(name): ModelPricing(
            model_id=values["id"],
            short=ContextPricing(**values["short_context"]),
            long=ContextPricing(**values["long_context"]),
            description=values["description"],
        )
        for name, values in data["models"].items()
    }
    return ModelCatalog(version=data["version"], models=models)
