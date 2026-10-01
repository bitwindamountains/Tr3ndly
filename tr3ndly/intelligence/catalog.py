"""Versioned need → generic product concept catalog.

Concepts are generic categories, never SKUs. An operator still has to confirm a real affiliate
listing before any content is produced. Execution and marketplace-fit values are provisional
priors; change them only together with a new CATALOG_VERSION.
"""

from dataclasses import dataclass

CATALOG_VERSION = "needs-catalog-v1"

NEED_LABELS: dict[str, str] = {
    "personal_cooling": "personal cooling",
    "hydration": "hydration",
    "sun_protection": "sun protection",
    "rain_protection": "rain protection",
    "dry_storage": "keeping belongings dry",
    "indoor_drying": "drying clothes indoors",
}


@dataclass(frozen=True)
class ProductConcept:
    key: str
    name: str
    category: str
    need: str
    target_user: str
    search_queries: tuple[str, ...]
    claims_to_avoid: tuple[str, ...]
    execution: int
    marketplace_fit_prior: int


CONCEPTS: tuple[ProductConcept, ...] = (
    ProductConcept(
        key="portable-rechargeable-fan",
        name="Portable rechargeable fan",
        category="Household convenience",
        need="personal_cooling",
        target_user="Commuters, students, and households",
        search_queries=(
            "portable rechargeable fan",
            "mini fan USB rechargeable",
            "handheld fan long battery",
        ),
        claims_to_avoid=("prevents heat stroke", "battery life not stated on the listing"),
        execution=85,
        marketplace_fit_prior=85,
    ),
    ProductConcept(
        key="cooling-towel",
        name="Instant cooling towel",
        category="Sports and outdoors",
        need="personal_cooling",
        target_user="Commuters and people who work outdoors",
        search_queries=("instant cooling towel", "cooling towel for neck", "ice towel sports"),
        claims_to_avoid=("lowers body temperature by a stated amount", "medical cooling"),
        execution=75,
        marketplace_fit_prior=75,
    ),
    ProductConcept(
        key="insulated-water-bottle",
        name="Insulated water bottle",
        category="Kitchen and dining",
        need="hydration",
        target_user="Students, office workers, and commuters",
        search_queries=(
            "insulated water bottle",
            "stainless tumbler cold 24 hours",
            "vacuum flask water bottle",
        ),
        claims_to_avoid=("cold-retention hours not stated on the listing", "health benefits"),
        execution=80,
        marketplace_fit_prior=85,
    ),
    ProductConcept(
        key="uv-umbrella",
        name="UV-protection umbrella",
        category="Fashion accessories",
        need="sun_protection",
        target_user="Commuters and students who walk outdoors",
        search_queries=("UV umbrella", "anti UV folding umbrella", "sun umbrella UPF"),
        claims_to_avoid=("blocks 100% of UV", "prevents skin cancer"),
        execution=75,
        marketplace_fit_prior=80,
    ),
    ProductConcept(
        key="compact-umbrella",
        name="Compact windproof umbrella",
        category="Fashion accessories",
        need="rain_protection",
        target_user="Commuters and students",
        search_queries=("compact windproof umbrella", "automatic folding umbrella"),
        claims_to_avoid=("typhoon-proof", "unbreakable"),
        execution=75,
        marketplace_fit_prior=85,
    ),
    ProductConcept(
        key="waterproof-shoe-covers",
        name="Reusable waterproof shoe covers",
        category="Shoes and accessories",
        need="rain_protection",
        target_user="Commuters and office workers",
        search_queries=("waterproof shoe cover reusable", "rain boots cover silicone"),
        claims_to_avoid=("flood-proof", "keeps feet dry in any water depth"),
        execution=80,
        marketplace_fit_prior=75,
    ),
    ProductConcept(
        key="waterproof-dry-bag",
        name="Waterproof dry bag",
        category="Travel and luggage",
        need="dry_storage",
        target_user="Commuters, riders, and students",
        search_queries=("waterproof dry bag", "dry bag 10L", "roll top waterproof bag"),
        claims_to_avoid=("fully submersible unless the listing says so",),
        execution=80,
        marketplace_fit_prior=75,
    ),
    ProductConcept(
        key="waterproof-phone-pouch",
        name="Waterproof phone pouch",
        category="Mobile accessories",
        need="dry_storage",
        target_user="Commuters and riders",
        search_queries=("waterproof phone pouch", "phone dry bag touchscreen"),
        claims_to_avoid=("an IPX rating not stated on the listing",),
        execution=85,
        marketplace_fit_prior=80,
    ),
    ProductConcept(
        key="foldable-drying-rack",
        name="Foldable indoor drying rack",
        category="Home and living",
        need="indoor_drying",
        target_user="Households, renters, and dorm residents",
        search_queries=("foldable clothes drying rack", "indoor drying rack stainless"),
        claims_to_avoid=("load capacity not stated on the listing",),
        execution=70,
        marketplace_fit_prior=80,
    ),
)


def concepts_for(needs: tuple[str, ...] | list[str]) -> list[ProductConcept]:
    return [concept for need in needs for concept in CONCEPTS if concept.need == need]
