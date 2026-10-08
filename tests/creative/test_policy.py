from tr3ndly.creative.policy import check_copy, has_blocking, normalize_hashtags

FACTS = ["USB-C charging", "3 speed settings", "4000mAh battery", "Water-resistant fabric"]


def codes(hook: str = "", caption: str = "", cta: str = "", facts: list[str] = FACTS) -> set[str]:
    issues = check_copy(hook=hook, caption=caption, cta=cta, hashtags=[], verified_facts=facts)
    return {issue["code"] for issue in issues}


def test_clean_copy_passes() -> None:
    issues = check_copy(
        hook="A practical fan for the hot days ahead.",
        caption="From the listing: USB-C charging, 3 speed settings, 4000mAh battery.",
        cta="Tap the link to see the listing.",
        hashtags=["#PortableFan"],
        verified_facts=FACTS,
    )
    assert issues == []


def test_claims_the_plan_forbids_are_blocked() -> None:
    assert "superlative" in codes(hook="The best fan this summer")
    assert "superlative" in codes(hook="Pinakamurang fan!")
    assert "urgency" in codes(caption="Hurry, limited stock!")
    assert "price" in codes(caption="Only ₱299 today")
    assert "price" in codes(caption="Grab the voucher")
    assert "health_safety" in codes(caption="Prevents heat stroke")
    assert "fear" in codes(hook="Don't get caught in the next disaster")
    assert "durability" in codes(caption="Totally unbreakable")


def test_numbers_and_durability_words_need_support_in_the_facts() -> None:
    assert "unverified_number" in codes(caption="Runs for 12 hours")
    assert "unverified_number" not in codes(caption="Has a 4000mAh battery")
    assert "unverified_number" not in codes(caption="Has a 4,000 mAh battery", facts=["4000mAh"])
    assert "durability" in codes(caption="Waterproof body")
    assert "durability" not in codes(caption="Waterproof body", facts=["Waterproof body"])
    # A "Bestseller" badge does not support the word "best".
    assert "superlative" in codes(hook="The best pick", facts=["Bestseller badge"])


def test_length_issues_warn_without_blocking() -> None:
    issues = check_copy(hook="x" * 200, caption="ok", cta="ok", hashtags=[], verified_facts=FACTS)
    assert [issue["code"] for issue in issues] == ["too_long"]
    assert not has_blocking(issues)


def test_hashtags_are_normalized() -> None:
    assert normalize_hashtags(["#portable fan", "Portable-Fan", "", "#ShopPH"]) == [
        "#PortableFan",
        "#ShopPH",
    ]
