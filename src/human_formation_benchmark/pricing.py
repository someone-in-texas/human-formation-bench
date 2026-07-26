"""Price matching, cost estimation, and concurrency-safe hard budget control."""

from __future__ import annotations

import asyncio
import fnmatch
from dataclasses import dataclass
from datetime import date

from .models import CostEstimate, PriceEntry, RunProfile


def find_price(model: str, prices: list[PriceEntry]) -> PriceEntry | None:
    matches = [
        item
        for item in prices
        if item.provider != "user_override_required" and fnmatch.fnmatch(model, item.model_pattern)
    ]
    return max(matches, key=lambda item: len(item.model_pattern), default=None)


def token_cost(
    input_tokens: int,
    output_tokens: int,
    *,
    input_per_million_usd: float,
    output_per_million_usd: float,
) -> float:
    return (
        input_tokens * input_per_million_usd + output_tokens * output_per_million_usd
    ) / 1_000_000


def estimate_run(
    profile: RunProfile,
    model: str,
    price: PriceEntry,
    budget_usd: float,
    *,
    sample_count: int | None = None,
) -> CostEstimate:
    samples = sample_count if sample_count is not None else profile.scenario_limit
    calls = samples * len(profile.policies) * len(profile.seeds) * profile.trajectory_turns
    judge_calls = calls * max(0, len(profile.judges) - 1)
    input_tokens = calls * min(profile.max_input_tokens, 900)
    output_tokens = calls * min(profile.max_output_tokens, 300)
    base = token_cost(
        input_tokens,
        output_tokens,
        input_per_million_usd=price.input_per_million_usd,
        output_per_million_usd=price.output_per_million_usd,
    )
    # Model judges usually consume the transcript and produce shorter outputs.
    base += judge_calls * token_cost(
        min(profile.max_input_tokens, 1800),
        min(profile.max_output_tokens, 250),
        input_per_million_usd=price.input_per_million_usd,
        output_per_million_usd=price.output_per_million_usd,
    )
    age = (date.today() - date.fromisoformat(price.last_verified_date)).days
    return CostEstimate(
        profile=profile.id,
        samples=samples,
        calls=calls + judge_calls,
        estimated_input_tokens=input_tokens + judge_calls * min(profile.max_input_tokens, 1800),
        estimated_output_tokens=output_tokens + judge_calls * min(profile.max_output_tokens, 250),
        low_usd=round(base * 0.6, 6),
        base_usd=round(base, 6),
        high_usd=round(base * 1.5, 6),
        budget_usd=budget_usd,
        price_data_stale=age > 90,
        assumptions=[
            "token use is estimated from profile caps rather than provider tokenization",
            "high estimate is 1.5x base and should be used for hard-cap planning",
            "the alpha makes no automatic retries; the reserve bounds usage-reporting deviations",
        ],
    )


class BudgetExceeded(RuntimeError):
    """Raised before a call that would breach the usable hard cap."""


@dataclass
class BudgetSnapshot:
    spent: float
    reserved: float
    usable_cap: float


class BudgetGuard:
    """Atomic budget reservations prevent concurrent calls from overspending."""

    def __init__(self, cap_usd: float, reserve_fraction: float = 0.10) -> None:
        if cap_usd <= 0:
            raise ValueError("budget cap must be positive")
        if not 0 <= reserve_fraction < 1:
            raise ValueError("reserve fraction must be in [0, 1)")
        self.cap_usd = cap_usd
        self.usable_cap = cap_usd * (1 - reserve_fraction)
        self.spent = 0.0
        self.reserved = 0.0
        self._condition = asyncio.Condition()

    async def reserve(self, estimated_high_usd: float) -> None:
        async with self._condition:
            # Provider-reported usage can violate advertised request caps. Serializing paid
            # reservations bounds that unavoidable deviation to one indivisible completed call.
            while estimated_high_usd > 0 and self.reserved > 0:
                await self._condition.wait()
            if self.spent + self.reserved + estimated_high_usd > self.usable_cap + 1e-12:
                raise BudgetExceeded(
                    f"next call reservation ${estimated_high_usd:.6f} would exceed "
                    f"usable cap ${self.usable_cap:.6f}"
                )
            self.reserved += estimated_high_usd

    async def settle(self, estimated_high_usd: float, actual_usd: float) -> BudgetSnapshot:
        async with self._condition:
            self.reserved = max(0.0, self.reserved - estimated_high_usd)
            self.spent += actual_usd
            self._condition.notify_all()
            if self.spent > self.cap_usd + 1e-12:
                raise BudgetExceeded("provider-reported cost exceeded the absolute hard cap")
            return self.snapshot()

    async def release(self, estimated_high_usd: float) -> None:
        async with self._condition:
            self.reserved = max(0.0, self.reserved - estimated_high_usd)
            self._condition.notify_all()

    def snapshot(self) -> BudgetSnapshot:
        return BudgetSnapshot(self.spent, self.reserved, self.usable_cap)
