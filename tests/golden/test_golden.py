import json
from pathlib import Path

from human_formation_benchmark.models import Dimension
from human_formation_benchmark.scoring import detect_failure_gates, deterministic_score


def test_golden_transcript_meets_expected_floor() -> None:
    root = Path(__file__).resolve().parents[2]
    fixture = json.loads((root / "data/fixtures/golden_transcript.json").read_text())
    assistant = fixture["messages"][1]["content"]
    results = deterministic_score(
        assistant,
        [Dimension.RELATEDNESS, Dimension.DEPENDENCY],
        message_index=1,
    )
    assert all(result.score is None and result.insufficient_evidence for result in results)
    assert all(
        any(flag.startswith("supportive_signal") for flag in result.flags) for result in results
    )
    assert (
        detect_failure_gates([assistant]).exclusivity_language
        is fixture["expected"]["exclusivity_language"]
    )
