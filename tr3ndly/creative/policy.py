"""Deterministic copy checks (plan sections 13 and 14).

Unsupported superlatives, urgency, prices, safety claims, durability claims, and performance
numbers fail validation. Superlatives, durability words, and numbers pass only when the
listing's verified facts contain them. Blocking issues prevent approval.
"""

import re
from dataclasses import dataclass
from typing import Any

POLICY_VERSION = "copy-policy-v1"

HOOK_MAX = 150
CAPTION_MAX = 1000
CTA_MAX = 120
HASHTAG_MAX = 6


@dataclass(frozen=True)
class _Rule:
    code: str
    pattern: re.Pattern[str]
    message: str
    # Allowed when the matched words also appear in the listing's verified facts.
    facts_can_support: bool


def _rule(code: str, pattern: str, message: str, facts_can_support: bool) -> _Rule:
    return _Rule(code, re.compile(pattern, re.IGNORECASE), message, facts_can_support)


RULES: tuple[_Rule, ...] = (
    _rule(
        "superlative",
        r"(?<!\w)(best|#\s?1|number one|no\.?\s?1|top[- ]rated|unbeatable|perfect|pinaka\w*)(?!\w)",
        "Unsupported superlative. Describe what the listing actually says.",
        facts_can_support=True,
    ),
    _rule(
        "urgency",
        r"\b(hurry|limited (?:time|stock|offer)|last chance|today only|only today|selling fast|"
        r"ubos na|while (?:supplies|stocks?) last|don'?t miss|act now)\b",
        "Urgency or scarcity claims are not allowed.",
        facts_can_support=False,
    ),
    _rule(
        "price",
        r"(₱|\bphp\s?\d|\b\d+(?:[.,]\d+)?\s?(?:pesos?|php)\b|\b\d{1,3}\s?%\s?off\b|"
        r"\bsale price\b|\bdiscount\w*|\bvouchers?\b|\bfree shipping\b|\bcheap(?:est)?\b|\bmura\b)",
        "Prices and discounts change. Send people to the listing instead.",
        facts_can_support=False,
    ),
    _rule(
        "health_safety",
        r"\b(guarantee\w*|cures?|cured|prevents?|prevention|treats?|heals?|medical|clinically|"
        r"doctor[- ]recommended|heat ?stroke|immunity|100% safe|safe for)\b",
        "Health, safety, and guarantee claims are not allowed.",
        facts_can_support=False,
    ),
    _rule(
        "durability",
        r"\b(unbreakable|indestructible|lasts? forever|lifetime|never breaks|"
        r"(?:typhoon|flood|water|shock|drop)[- ]?proof|heavy[- ]duty)\b",
        "Durability claim not supported by the listing's verified facts.",
        facts_can_support=True,
    ),
    _rule(
        "fear",
        r"\b(disaster|deadly|deaths?|die|dying|emergency|calamity|danger(?:ous)?|bagyo|baha|"
        r"panic)\b",
        "Do not use fear or disaster framing to sell.",
        facts_can_support=False,
    ),
)

# A number followed by a unit is a performance or spec claim.
_NUMBER_WITH_UNIT = re.compile(
    r"\b(\d+(?:[.,]\d+)?)\s?(mah|hours?|hrs?|days?|°c|%|watts?|w|liters?|l|ml|kg|g|db|"
    r"inch(?:es)?|cm|mm|meters?|m|x|pcs|pieces|speeds?|layers?|in 1)(?![a-z])",
    re.IGNORECASE,
)
_NUMBER = re.compile(r"\d+(?:[.,]\d+)?")


def _number_key(text: str) -> str:
    return text.replace(",", "")


def _in_facts(phrase: str, facts_text: str) -> bool:
    """Whole-word match, so a "Bestseller" badge does not support the word "best"."""
    return re.search(rf"(?<!\w){re.escape(phrase.lower())}(?!\w)", facts_text) is not None


def check_copy(
    *, hook: str, caption: str, cta: str, hashtags: list[str], verified_facts: list[str]
) -> list[dict[str, Any]]:
    """Return policy issues as plain dicts (stored on the variant as JSON)."""
    facts_text = " ".join(verified_facts).lower()
    fact_numbers = {_number_key(number) for number in _NUMBER.findall(facts_text)}
    fields = {"hook": hook, "caption": caption, "cta": cta, "hashtags": " ".join(hashtags)}

    issues: list[dict[str, Any]] = []
    seen: set[tuple[str, str, str]] = set()

    def add(code: str, field: str, match: str, message: str, blocking: bool = True) -> None:
        key = (code, field, match.lower())
        if key not in seen:
            seen.add(key)
            issues.append(
                {
                    "code": code,
                    "field": field,
                    "match": match,
                    "message": message,
                    "blocking": blocking,
                }
            )

    for field, text in fields.items():
        for rule in RULES:
            for found in rule.pattern.finditer(text):
                matched = found.group(0)
                if rule.facts_can_support and _in_facts(matched, facts_text):
                    continue
                add(rule.code, field, matched, rule.message)
        for found in _NUMBER_WITH_UNIT.finditer(text):
            if _number_key(found.group(1)) not in fact_numbers:
                add(
                    "unverified_number",
                    field,
                    found.group(0),
                    "Numbers and specs must appear in the listing's verified facts.",
                )

    for field, limit, text in (
        ("hook", HOOK_MAX, hook),
        ("caption", CAPTION_MAX, caption),
        ("cta", CTA_MAX, cta),
    ):
        if len(text) > limit:
            add(
                "too_long",
                field,
                f"{len(text)} characters",
                f"Keep it under {limit} characters.",
                False,
            )
    if len(hashtags) > HASHTAG_MAX:
        add(
            "too_many_hashtags",
            "hashtags",
            f"{len(hashtags)} hashtags",
            f"Use at most {HASHTAG_MAX} hashtags.",
            False,
        )
    return issues


def has_blocking(issues: list[dict[str, Any]]) -> bool:
    return any(issue.get("blocking") for issue in issues)


def normalize_hashtags(hashtags: list[str]) -> list[str]:
    """`#Like This` and `like-this` both become `#LikeThis`; duplicates and empties are dropped."""
    normalized: list[str] = []
    for tag in hashtags:
        words = re.findall(r"[A-Za-z0-9]+", tag)
        if not words:
            continue
        joined = "#" + "".join(word[:1].upper() + word[1:] for word in words)
        if joined.lower() not in {existing.lower() for existing in normalized}:
            normalized.append(joined)
    return normalized
