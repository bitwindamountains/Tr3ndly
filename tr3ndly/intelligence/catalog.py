"""Versioned need → generic product concept catalog.

Concepts are generic categories, never SKUs. An operator still has to confirm a real affiliate
listing before any content is produced. Execution and marketplace-fit values are provisional
priors; change them only together with a new CATALOG_VERSION.
"""

from dataclasses import dataclass

CATALOG_VERSION = "needs-catalog-v2"

NEED_LABELS: dict[str, str] = {
    "personal_cooling": "personal cooling",
    "hydration": "hydration",
    "sun_protection": "sun protection",
    "rain_protection": "rain protection",
    "dry_storage": "keeping belongings dry",
    "indoor_drying": "drying clothes indoors",
    "sale_day_upgrades": "buying a bigger-ticket item on a sale day",
    "gift_giving": "finding a gift",
    "school_supplies": "getting ready for school",
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
    ProductConcept(
        key="air-fryer",
        name="Air fryer",
        category="Kitchen appliances",
        need="sale_day_upgrades",
        target_user="Households and young professionals",
        search_queries=("air fryer 4L", "digital air fryer", "air fryer oven"),
        claims_to_avoid=("oil-free or healthier cooking", "capacity or wattage not on the listing"),
        execution=80,
        marketplace_fit_prior=85,
    ),
    ProductConcept(
        key="wireless-earbuds",
        name="Wireless earbuds",
        category="Mobile accessories",
        need="sale_day_upgrades",
        target_user="Students, commuters, and office workers",
        search_queries=("TWS wireless earbuds", "bluetooth earbuds", "earbuds with charging case"),
        claims_to_avoid=(
            "battery hours not stated on the listing",
            "noise cancellation unless the listing says so",
        ),
        execution=80,
        marketplace_fit_prior=85,
    ),
    ProductConcept(
        key="robot-vacuum",
        name="Robot vacuum cleaner",
        category="Home appliances",
        need="sale_day_upgrades",
        target_user="Households, pet owners, and busy professionals",
        search_queries=("robot vacuum cleaner", "robot vacuum mop 2 in 1"),
        claims_to_avoid=("suction power not stated on the listing", "allergy or health benefits"),
        execution=70,
        marketplace_fit_prior=70,
    ),
    ProductConcept(
        key="bluetooth-speaker",
        name="Portable Bluetooth speaker",
        category="Audio",
        need="gift_giving",
        target_user="Gift buyers for friends, partners, and parents",
        search_queries=("portable bluetooth speaker", "mini speaker wireless"),
        claims_to_avoid=("a waterproof rating not stated on the listing", "battery hours"),
        execution=80,
        marketplace_fit_prior=80,
    ),
    ProductConcept(
        key="scented-candle-gift-set",
        name="Scented candle gift set",
        category="Home and living",
        need="gift_giving",
        target_user="Gift buyers on a budget",
        search_queries=("scented candle gift set", "aromatherapy candle gift box"),
        claims_to_avoid=("stress relief, sleep, or other health benefits",),
        execution=75,
        marketplace_fit_prior=75,
    ),
    ProductConcept(
        key="fitness-smartwatch",
        name="Fitness smartwatch",
        category="Wearables",
        need="gift_giving",
        target_user="Gift buyers for active friends and family",
        search_queries=("fitness smartwatch", "smart watch heart rate", "smart band"),
        claims_to_avoid=("medical-grade heart-rate or blood-oxygen accuracy", "battery days"),
        execution=75,
        marketplace_fit_prior=80,
    ),
    ProductConcept(
        key="school-backpack",
        name="School backpack",
        category="Bags",
        need="school_supplies",
        target_user="Parents and students",
        search_queries=("school backpack", "laptop backpack student", "kids school bag"),
        claims_to_avoid=("waterproof unless the listing says so", "posture or spine benefits"),
        execution=80,
        marketplace_fit_prior=85,
    ),
    ProductConcept(
        key="insulated-lunch-box",
        name="Insulated lunch box",
        category="Kitchen and dining",
        need="school_supplies",
        target_user="Parents, students, and office workers",
        search_queries=("insulated lunch box", "bento box with bag", "lunch bag thermal"),
        claims_to_avoid=("keeps food safe for a stated number of hours", "BPA-free unless stated"),
        execution=75,
        marketplace_fit_prior=80,
    ),
    ProductConcept(
        key="led-desk-lamp",
        name="LED desk lamp",
        category="Home and living",
        need="school_supplies",
        target_user="Students studying at home",
        search_queries=("LED desk lamp", "study lamp rechargeable", "desk lamp eye care"),
        claims_to_avoid=("eye protection or myopia prevention",),
        execution=75,
        marketplace_fit_prior=80,
    ),
)


CONCEPTS_BY_KEY = {concept.key: concept for concept in CONCEPTS}


def concepts_for(needs: tuple[str, ...] | list[str]) -> list[ProductConcept]:
    return [concept for need in needs for concept in CONCEPTS if concept.need == need]
