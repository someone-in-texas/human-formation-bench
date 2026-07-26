import asyncio

import pytest

from human_formation_benchmark.config import load_profile
from human_formation_benchmark.models import PriceEntry
from human_formation_benchmark.pricing import (
    BudgetExceeded,
    BudgetGuard,
    estimate_run,
    token_cost,
)


def price() -> PriceEntry:
    return PriceEntry(
        provider="test",
        model_pattern="test/*",
        input_per_million_usd=1,
        output_per_million_usd=2,
        effective_date="2026-07-25",
        source_url="test",
        last_verified_date="2026-07-25",
    )


def test_token_cost() -> None:
    assert (
        token_cost(
            1_000_000,
            500_000,
            input_per_million_usd=1,
            output_per_million_usd=2,
        )
        == 2
    )


def test_plan_has_ordered_uncertainty() -> None:
    estimate = estimate_run(load_profile("micro"), "test/model", price(), 5, sample_count=2)
    assert estimate.low_usd <= estimate.base_usd <= estimate.high_usd
    assert estimate.calls > 0


@pytest.mark.asyncio
async def test_budget_reservations_are_atomic() -> None:
    guard = BudgetGuard(1, reserve_fraction=0)
    await guard.reserve(0.6)
    waiting = asyncio.create_task(guard.reserve(0.5))
    await asyncio.sleep(0)
    assert not waiting.done()
    snapshot = await guard.settle(0.6, 0.4)
    assert snapshot.spent == 0.4
    await waiting


@pytest.mark.asyncio
async def test_budget_never_silently_exceeds_absolute_cap() -> None:
    guard = BudgetGuard(1, reserve_fraction=0)
    await guard.reserve(0.9)
    with pytest.raises(BudgetExceeded):
        await guard.settle(0.9, 1.1)


@pytest.mark.asyncio
async def test_reported_cost_deviation_is_bounded_to_one_in_flight_call() -> None:
    guard = BudgetGuard(0.1, reserve_fraction=0)
    first_admitted = asyncio.Event()

    async def expensive_call() -> None:
        await guard.reserve(0.01)
        first_admitted.set()
        await asyncio.sleep(0.01)
        await guard.settle(0.01, 1)

    async def queued_call() -> None:
        await first_admitted.wait()
        await guard.reserve(0.01)

    results = await asyncio.gather(
        expensive_call(),
        queued_call(),
        return_exceptions=True,
    )
    assert all(isinstance(result, BudgetExceeded) for result in results)
    assert guard.spent == 1
