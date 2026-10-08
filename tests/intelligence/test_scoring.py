from tr3ndly.db.models import Sensitivity
from tr3ndly.intelligence.catalog import CONCEPTS, NEED_LABELS, concepts_for
from tr3ndly.intelligence.scoring import (
    ListingFacts,
    TimelyDimensions,
    demand_score,
    discovery_priority,
    expected_commission_centavos,
    listing_economics,
    score_concept,
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


def listing(**overrides: object) -> ListingFacts:
    values: dict[str, object] = {
        "price_centavos": 59_900,
        "commission_rate_bps": 800,
        "rating_tenths": 48,
        "review_count": 1200,
        "sold_count": 5000,
        "seller_type": "mall",
    }
    values.update(overrides)
    return ListingFacts(**values)  # type: ignore[arg-type]


def test_economics_rewards_commission_amount_not_rate() -> None:
    # 20% of PHP 50 (PHP 10) earns less than 5% of PHP 999 (about PHP 50).
    cheap, _ = listing_economics(listing(price_centavos=5_000, commission_rate_bps=2000))
    pricier, _ = listing_economics(listing(price_centavos=99_900, commission_rate_bps=500))
    assert pricier > cheap
    assert expected_commission_centavos(99_900, 500) == 4_995


def test_economics_pulls_thin_review_evidence_toward_neutral() -> None:
    _, proven = listing_economics(listing(rating_tenths=49, review_count=500))
    _, thin = listing_economics(listing(rating_tenths=49, review_count=5))
    assert proven["rating"] > thin["rating"] >= 50


def test_confirmed_listing_switches_to_publish_priority() -> None:
    dimensions = TimelyDimensions(100, 100, 100, 70, 85, 70, 0)
    concept = CONCEPTS[0]
    before = score_concept(dimensions, concept, 0, Sensitivity.LOW)
    after = score_concept(dimensions, concept, 0, Sensitivity.LOW, listing())

    assert before.version == "discovery-v2" and before.publish_priority is None
    assert after.version == "publish-v1"
    assert after.listing_economics is not None and after.publish_priority is not None
    # Matching a listing removes the "no listing yet" uncertainty.
    assert after.uncertainty == before.uncertainty - 5
