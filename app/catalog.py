"""Versioned model catalog and cost calculations."""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import yaml

from app.models import CostEstimate, ModelTier


@dataclass(frozen=True)
class ModelPricing:
    model_id: str
    input_per_million: float
    output_per_million: float
    cached_input_per_million: float
    description: str


class ModelCatalog:
    def __init__(self, version: str, models: dict[ModelTier, ModelPricing]) -> None:
        self.version = version
        self.models = models

    def model_id(self, tier: ModelTier) -> str:
        return self.models[tier].model_id

    def estimate(self, tier: ModelTier, input_tokens: int, output_tokens: int) -> CostEstimate:
        pricing = self.models[tier]
        amount = (
            input_tokens * pricing.input_per_million + output_tokens * pricing.output_per_million
        ) / 1_000_000
        return CostEstimate(
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            estimated_usd=round(amount, 8),
            pricing_version=self.version,
        )

    def public_models(self) -> dict[str, dict[str, str | float]]:
        return {
            tier.value: {
                "id": pricing.model_id,
                "input_per_million": pricing.input_per_million,
                "output_per_million": pricing.output_per_million,
                "cached_input_per_million": pricing.cached_input_per_million,
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
            input_per_million=float(values["input_per_million"]),
            output_per_million=float(values["output_per_million"]),
            cached_input_per_million=float(values["cached_input_per_million"]),
            description=values["description"],
        )
        for name, values in data["models"].items()
    }
    return ModelCatalog(version=data["version"], models=models)
