import json
from types import SimpleNamespace
from typing import Any

import pytest

from tests.conftest import FIXTURES
from tr3ndly.config import Settings
from tr3ndly.creative.copywriter import (
    BriefInput,
    ClaudeCopywriter,
    TemplateCopywriter,
    build_copywriter,
)
from tr3ndly.creative.policy import check_copy
from tr3ndly.creative.prompts import COPY_PROMPT_VERSION
from tr3ndly.errors import UpstreamError


def fixture_briefs() -> list[BriefInput]:
    items = json.loads((FIXTURES / "copy_briefs.json").read_text(encoding="utf-8"))
    return [
        BriefInput(
            **{
                **item,
                "verified_facts": tuple(item["verified_facts"]),
                "forbidden_claims": tuple(item["forbidden_claims"]),
            }
        )
        for item in items
    ]


@pytest.mark.parametrize("brief", fixture_briefs(), ids=lambda brief: brief.product_name)
async def test_template_copy_passes_policy_for_every_fixture_brief(brief: BriefInput) -> None:
    batch = await TemplateCopywriter().write(brief)

    assert [draft.hook_type for draft in batch.drafts] == ["problem", "benefit", "curiosity"]
    for draft in batch.drafts:
        issues = check_copy(
            hook=draft.hook,
            caption=draft.caption,
            cta=draft.cta,
            hashtags=draft.hashtags,
            verified_facts=list(brief.verified_facts),
        )
        assert issues == [], (draft, issues)


class FakeMessages:
    def __init__(self, response: Any) -> None:
        self.response = response
        self.calls: list[dict[str, Any]] = []

    async def create(self, **kwargs: Any) -> Any:
        self.calls.append(kwargs)
        return self.response


def fake_client(response: Any) -> Any:
    return SimpleNamespace(beta=SimpleNamespace(messages=FakeMessages(response)))


def model_response(text: str, stop_reason: str = "end_turn") -> Any:
    return SimpleNamespace(
        stop_reason=stop_reason,
        content=[SimpleNamespace(type="thinking"), SimpleNamespace(type="text", text=text)],
        model="claude-opus-5-5",
        usage=SimpleNamespace(input_tokens=900, output_tokens=400),
        _request_id="req_test",
    )


VARIANTS = {
    "variants": [
        {
            "hook_type": kind,
            "hook": f"{kind} hook",
            "caption": "From the listing: USB-C charging.",
            "cta": "Tap the link.",
            "hashtags": ["#Fan"],
        }
        for kind in ("problem", "benefit", "curiosity")
    ]
}


async def test_claude_copywriter_sends_a_structured_request_and_parses_it() -> None:
    client = fake_client(model_response(json.dumps(VARIANTS)))
    writer = ClaudeCopywriter("claude-opus-5-5", client=client)

    batch = await writer.write(fixture_briefs()[0])

    call = client.beta.messages.calls[0]
    assert call["model"] == "claude-opus-5-5"
    assert call["fallbacks"] == "default"
    assert call["betas"] == ["server-side-fallback-2026-07-01"]
    assert call["output_config"]["format"]["type"] == "json_schema"
    assert "4000mAh battery" in call["messages"][0]["content"]
    assert [draft.hook_type for draft in batch.drafts] == ["problem", "benefit", "curiosity"]
    assert batch.generator == "claude:claude-opus-5-5"
    assert batch.prompt_version == COPY_PROMPT_VERSION
    assert batch.generation == {
        "model": "claude-opus-5-5",
        "request_id": "req_test",
        "input_tokens": 900,
        "output_tokens": 400,
    }


@pytest.mark.parametrize(
    ("response", "message"),
    [
        (model_response("", stop_reason="refusal"), "declined"),
        (model_response("{}", stop_reason="max_tokens"), "cut off"),
        (model_response('{"variants": "nope"}'), "invalid output"),
    ],
)
async def test_claude_copywriter_failures_raise_upstream_errors(
    response: Any, message: str
) -> None:
    writer = ClaudeCopywriter("claude-opus-5-5", client=fake_client(response))
    with pytest.raises(UpstreamError, match=message):
        await writer.write(fixture_briefs()[0])


def test_template_is_used_without_an_api_key() -> None:
    assert isinstance(build_copywriter(Settings(anthropic_api_key=None)), TemplateCopywriter)
    assert isinstance(build_copywriter(Settings(anthropic_api_key="sk-test")), ClaudeCopywriter)


async def test_template_uses_the_right_article() -> None:
    brief = next(item for item in fixture_briefs() if item.product_name == "Air fryer")
    curiosity = (await TemplateCopywriter().write(brief)).drafts[2]
    assert curiosity.hook.startswith("Thinking of getting an air fryer?")
