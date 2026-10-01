from tr3ndly.db.models import Sensitivity
from tr3ndly.intelligence.catalog import CONCEPTS, NEED_LABELS, concepts_for
from tr3ndly.intelligence.scoring import (
    TimelyDimensions,
    demand_score,
    discovery_priority,
    uncertainty_penalty,
)


def test_timely_score_follows_the_plan_weights() -> None:
    dimensions = TimelyDimensions(
        freshness=100,
        geography=100,
        reach=100,
        need_strength=60,
        actionability=85,
        source_confidence=70,
        sensitivity_penalty=0,
    )
    # 15 + 15 + 10 + 15 + 17 + 10.5 = 82.5, rounded half to even.
    assert dimensions.score() == 82


def test_scores_are_clamped() -> None:
    blocked = TimelyDimensions(10, 10, 10, 10, 10, 10, sensitivity_penalty=100)
    assert blocked.score() == 0
    assert discovery_priority(100, 100, 100, 0) == 100


def test_demand_rewards_agreement_without_requiring_it() -> None:
    assert demand_score(80, None) == 80
    assert demand_score(80, 40) == 86
    assert demand_score(95, 90) == 100


def test_uncertainty_grows_with_lead_time_and_sensitivity() -> None:
    assert uncertainty_penalty(0, Sensitivity.LOW) == 5
    assert uncertainty_penalty(2, Sensitivity.LOW) == 15
    assert uncertainty_penalty(1, Sensitivity.MEDIUM) == 15


def test_every_concept_has_a_known_need_and_search_queries() -> None:
    keys = [concept.key for concept in CONCEPTS]
    assert len(keys) == len(set(keys))
    for concept in CONCEPTS:
        assert concept.need in NEED_LABELS
        assert concept.search_queries
        assert concept.claims_to_avoid
    assert [c.key for c in concepts_for(["hydration"])] == ["insulated-water-bottle"]
