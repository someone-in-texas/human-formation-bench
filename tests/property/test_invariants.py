from hypothesis import given
from hypothesis import strategies as st

from human_formation_benchmark.hashing import content_hash
from human_formation_benchmark.models import Dimension
from human_formation_benchmark.scoring import deterministic_score
from human_formation_benchmark.security import redact


@given(st.text(max_size=200))
def test_deterministic_score_stays_in_bounds(text: str) -> None:
    results = deterministic_score(text, list(Dimension), message_index=0)
    assert all(result.score is None or 0 <= result.score <= 4 for result in results)


@given(st.dictionaries(st.text(min_size=1, max_size=10), st.integers(), max_size=10))
def test_hash_is_repeatable(payload: dict[str, int]) -> None:
    assert content_hash(payload) == content_hash(payload)


@given(st.text(max_size=200))
def test_redaction_is_idempotent(text: str) -> None:
    assert redact(redact(text)) == redact(text)
