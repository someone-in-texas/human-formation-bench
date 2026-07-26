from pathlib import Path

import pytest

from human_formation_benchmark.models import Message, PriceEntry, ProviderResponse, TokenUsage
from human_formation_benchmark.pricing import find_price
from human_formation_benchmark.providers import FakeProvider
from human_formation_benchmark.storage import ContentCache


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "policy",
    [
        "default_assistant",
        "agreeable_sycophantic_control",
        "socratic_agency_support",
        "human_standing_governance",
        "christian_flourishing",
        "secular_pluralist_flourishing",
        "multi_agent_council",
    ],
)
async def test_fake_provider_is_deterministic_and_covers_policies(policy: str) -> None:
    provider = FakeProvider()
    messages = [Message(role="user", content="Help me decide what to do.")]
    first = await provider.generate(messages, policy_id=policy, seed=7, max_output_tokens=100)
    second = await provider.generate(messages, policy_id=policy, seed=7, max_output_tokens=100)
    assert first.text == second.text
    assert first.provider_request_id == second.provider_request_id
    assert first.cost_usd == 0


def test_content_cache_round_trip_and_prune(tmp_path: Path) -> None:
    cache = ContentCache(tmp_path)
    key = cache.key({"prompt": "synthetic"})
    assert cache.get(key) is None
    response = ProviderResponse(
        text="response",
        usage=TokenUsage(input_tokens=1, output_tokens=2),
        latency_ms=3,
        cost_usd=0,
    )
    cache.put(key, response)
    assert cache.get(key) == response
    assert cache.count() == 1
    assert cache.prune() == 1
    assert cache.count() == 0


def test_price_matching_prefers_specific_pattern() -> None:
    prices = [
        PriceEntry(
            provider="x",
            model_pattern="x/*",
            input_per_million_usd=1,
            output_per_million_usd=1,
            effective_date="2026-01-01",
            source_url="x",
            last_verified_date="2026-01-01",
        ),
        PriceEntry(
            provider="x",
            model_pattern="x/specific",
            input_per_million_usd=2,
            output_per_million_usd=2,
            effective_date="2026-01-01",
            source_url="x",
            last_verified_date="2026-01-01",
        ),
    ]
    assert find_price("x/specific", prices) == prices[1]
    assert find_price("other/model", prices) is None
