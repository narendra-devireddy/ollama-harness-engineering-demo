from harness_demo.domain import Lane
from harness_demo.runners import RUNNERS
from harness_demo.scenarios import load_incident_scenario


def test_hand_built_harness_scores_full_marks() -> None:
    scenario = load_incident_scenario("incident-response")
    result = RUNNERS[Lane.HAND_BUILT](scenario)
    assert result.score == 100
    assert all(result.checks.values())


def test_raw_strong_model_fails_harness_checks() -> None:
    scenario = load_incident_scenario("incident-response")
    result = RUNNERS[Lane.RAW_STRONG](scenario)
    assert result.score < 100
    assert not result.checks["runbook"]
    assert not result.checks["safety"]


def test_strands_lane_matches_hand_built_quality() -> None:
    scenario = load_incident_scenario("incident-response")
    hand_built = RUNNERS[Lane.HAND_BUILT](scenario)
    strands = RUNNERS[Lane.STRANDS_SDK](scenario)
    assert strands.score == hand_built.score
