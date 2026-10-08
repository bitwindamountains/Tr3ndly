"""The operator flow from an accepted opportunity to imported results, through the API."""

from typing import Any

from fastapi.testclient import TestClient

LISTING: dict[str, Any] = {
    "marketplace": "shopee",
    "product_url": "https://shopee.ph/product/123/456",
    "affiliate_url": "https://s.shopee.ph/abc123",
    "listing_title": "Mini Rechargeable Handheld Fan USB-C",
    "seller_name": "Cool Gadgets PH",
    "seller_type": "preferred",
    "price_php": "349.00",
    "commission_rate_pct": "8.5",
    "rating": "4.8",
    "review_count": 2400,
    "sold_count": 10000,
    "in_stock": True,
    "verified_facts": ["USB-C charging", "3 speed settings", "  3 speed settings  ", ""],
    "image_url": "https://example.com/fan.jpg",
}


def first_opportunity(client: TestClient) -> dict[str, Any]:
    return client.get("/today").json()["opportunities"][0]


def accept(client: TestClient, opportunity_id: str) -> None:
    response = client.post(
        f"/opportunities/{opportunity_id}/decision",
        json={"decision": "accepted", "reason_code": "useful_opportunity"},
    )
    assert response.status_code == 201


def matched_listing(client: TestClient) -> tuple[str, dict[str, Any]]:
    opportunity = first_opportunity(client)
    accept(client, opportunity["id"])
    match = client.post(f"/opportunities/{opportunity['id']}/product-match", json=LISTING).json()
    confirmed = client.post(
        f"/product-matches/{match['id']}/confirm", json={"eligibility_confirmed": True}
    )
    assert confirmed.status_code == 200
    return opportunity["id"], confirmed.json()


def test_listings_need_an_accepted_opportunity(live_client: TestClient) -> None:
    opportunity = first_opportunity(live_client)
    response = live_client.post(f"/opportunities/{opportunity['id']}/product-match", json=LISTING)
    assert response.status_code == 409
    assert "Accept the opportunity" in response.json()["detail"]


def test_confirming_a_listing_rescores_with_economics(live_client: TestClient) -> None:
    opportunity_id, match = matched_listing(live_client)

    assert match["status"] == "confirmed"
    assert match["price_php"] == 349.0
    assert match["commission_rate_pct"] == 8.5
    assert match["expected_commission_php"] == 29.66
    assert match["rating"] == 4.8
    assert match["verified_facts"] == ["USB-C charging", "3 speed settings"]

    detail = live_client.get(f"/opportunities/{opportunity_id}").json()
    assert detail["status"] == "matched"
    assert detail["decidable"] is False and detail["matchable"] is True
    assert detail["score"]["version"] == "publish-v1"
    assert detail["score"]["publish_priority"] is not None
    assert detail["score"]["listing_economics"] == match["listing_economics"]
    assert "No affiliate listing has been matched yet." not in detail["uncertainties"]


def test_out_of_stock_listings_cannot_be_confirmed(live_client: TestClient) -> None:
    opportunity = first_opportunity(live_client)
    accept(live_client, opportunity["id"])
    match = live_client.post(
        f"/opportunities/{opportunity['id']}/product-match", json={**LISTING, "in_stock": False}
    ).json()
    response = live_client.post(
        f"/product-matches/{match['id']}/confirm", json={"eligibility_confirmed": True}
    )
    assert response.status_code == 409


def test_a_newer_confirmed_listing_replaces_the_old_one(live_client: TestClient) -> None:
    opportunity_id, first = matched_listing(live_client)
    second = live_client.post(
        f"/opportunities/{opportunity_id}/product-match",
        json={**LISTING, "listing_title": "Another fan"},
    ).json()
    live_client.post(
        f"/product-matches/{second['id']}/confirm", json={"eligibility_confirmed": True}
    )

    statuses = {
        item["id"]: item["status"]
        for item in live_client.get(f"/opportunities/{opportunity_id}").json()["product_matches"]
    }
    assert statuses == {first["id"]: "stale", second["id"]: "confirmed"}
    stale = live_client.post(
        f"/product-matches/{first['id']}/creative-brief", json={"platform": "tiktok"}
    )
    assert stale.status_code == 409


def test_failed_searches_are_logged(live_client: TestClient) -> None:
    opportunity = first_opportunity(live_client)
    response = live_client.post(
        f"/opportunities/{opportunity['id']}/search-failures",
        json={"marketplace": "lazada", "query": "handheld fan", "reason": "low_commission"},
    )
    assert response.status_code == 201
    detail = live_client.get(f"/opportunities/{opportunity['id']}").json()
    assert [item["reason"] for item in detail["search_failures"]] == ["low_commission"]


def test_brief_to_export_to_results(live_client: TestClient) -> None:
    _, match = matched_listing(live_client)

    brief = live_client.post(
        f"/product-matches/{match['id']}/creative-brief",
        json={"platform": "tiktok", "experiment_label": "heat-fan-A"},
    ).json()
    assert brief["angle"] == "A practical portable rechargeable fan for the hot days ahead."
    assert "prevents heat stroke" in brief["forbidden_claims"]

    variants = live_client.post(f"/creative-briefs/{brief['id']}/generate").json()
    assert len(variants) == 3
    assert all(variant["generator"] == "template" for variant in variants)
    assert all(variant["policy_issues"] == [] for variant in variants)
    variant = variants[0]

    early = live_client.post(f"/creatives/{variant['id']}/export")
    assert early.status_code == 409

    approved = live_client.post(
        f"/creatives/{variant['id']}/review", json={"decision": "approved"}
    ).json()
    assert approved["status"] == "approved"

    package = live_client.post(f"/creatives/{variant['id']}/export").json()
    code = package["tracking_code"]
    assert code.startswith("t3") and len(code) == 10
    assert package["post_text"].endswith("#PortableRechargeableFan #HouseholdConvenience")
    assert "I may earn a commission" in package["post_text"]
    assert package["affiliate_url"] == LISTING["affiliate_url"]
    assert any("heat-fan-A" in step for step in package["checklist"])
    # Exporting again returns the same package and code.
    assert live_client.post(f"/creatives/{variant['id']}/export").json()["tracking_code"] == code
    assert live_client.get(f"/creatives/{variant['id']}/export").json()["tracking_code"] == code

    csv_text = (
        "Sub_id1,Date,Clicks,Orders,Commission\n"
        f'{code},2026-10-02,120,4,"₱118.64"\n'
        "manual-post,10/02/2026,80,1,29.66\n"
        f"{code},not-a-date,1,1,1\n"
    )
    result = live_client.post("/results/import", json={"csv": csv_text}).json()
    assert result["imported"] == 2
    assert result["baseline_codes"] == ["manual-post"]
    assert result["errors"] and result["errors"][0].startswith("Line 4")
    again = live_client.post("/results/import", json={"csv": csv_text}).json()
    assert again["imported"] == 0 and again["unchanged"] == 2

    overview = live_client.get("/results/overview").json()
    assert overview["assisted"]["posts"] == 1
    assert overview["assisted"]["commission_php"] == 118.64
    assert overview["assisted"]["conversion_rate"] == round(4 / 120, 4)
    assert overview["baseline"]["commission_php"] == 29.66
    assert [group["key"] for group in overview["by_event_type"]] == ["HEAT"]
    assert any("at least 30" in warning for warning in overview["warnings"])


def test_edits_with_unsupported_claims_are_saved_but_not_approved(
    live_client: TestClient,
) -> None:
    _, match = matched_listing(live_client)
    brief = live_client.post(
        f"/product-matches/{match['id']}/creative-brief", json={"platform": "facebook"}
    ).json()
    variant = live_client.post(f"/creative-briefs/{brief['id']}/generate").json()[0]

    response = live_client.post(
        f"/creatives/{variant['id']}/review",
        json={
            "decision": "approved",
            "edits": {
                "hook": "The best fan, only ₱349!",
                "caption": "Runs 12 hours.",
                "cta": "Hurry!",
                "hashtags": ["fan"],
            },
        },
    )
    assert response.status_code == 409

    studio = live_client.get(f"/product-matches/{match['id']}/studio").json()
    edited = [
        item for item in studio["briefs"][0]["variants"] if item["parent_id"] == variant["id"]
    ]
    assert len(edited) == 1
    assert edited[0]["status"] == "needs_review"
    assert {issue["code"] for issue in edited[0]["policy_issues"]} >= {
        "superlative",
        "price",
        "unverified_number",
        "urgency",
    }
    assert studio["generator"] == "template"


def test_results_import_rejects_csv_without_required_columns(live_client: TestClient) -> None:
    response = live_client.post("/results/import", json={"csv": "foo,bar\n1,2\n"})
    assert response.status_code == 422
