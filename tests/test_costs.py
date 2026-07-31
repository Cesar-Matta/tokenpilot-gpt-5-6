from app.catalog import get_catalog
from app.models import ModelTier


def test_long_context_uses_long_context_rates() -> None:
    catalog = get_catalog()
    short = catalog.estimate(ModelTier.SOL, 200_000, 10_000)
    long = catalog.estimate(ModelTier.SOL, 200_000, 10_000, long_context=True)

    assert short.context_band == "short"
    assert long.context_band == "long"
    assert long.estimated_usd > short.estimated_usd


def test_cache_rates_are_applied_without_double_counting_input() -> None:
    estimate = get_catalog().estimate(
        ModelTier.LUNA,
        1_000_000,
        0,
        cached_input_tokens=500_000,
        cache_write_tokens=250_000,
    )

    assert estimate.estimated_usd == 0.1225
    assert estimate.cached_input_tokens == 500_000
    assert estimate.cache_write_tokens == 250_000
