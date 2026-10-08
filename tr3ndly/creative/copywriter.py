"""Copywriters turn a brief into copy drafts. Neither one stores anything.

`ClaudeCopywriter` is used when ANTHROPIC_API_KEY is set; `TemplateCopywriter` otherwise. Both
outputs go through the same policy checks and human review.
"""

import re
from dataclasses import asdict, dataclass, field
from typing import Any, Literal, Protocol

import anthropic
from pydantic import BaseModel, Field, ValidationError

from tr3ndly.config import Settings
from tr3ndly.creative.prompts import COPY_PROMPT_VERSION, COPY_SCHEMA, SYSTEM_PROMPT, render_brief
from tr3ndly.errors import UpstreamError

TEMPLATE_VERSION = "copy-template-v1"
VARIANTS_PER_BRIEF = 3


@dataclass(frozen=True)
class BriefInput:
    product_name: str
    category: str
    platform: str
    audience: str
    angle: str
    verified_facts: tuple[str, ...]
    forbidden_claims: tuple[str, ...]


@dataclass(frozen=True)
class CopyDraft:
    hook_type: str
    hook: str
    caption: str
    cta: str
    hashtags: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class CopyBatch:
    drafts: list[CopyDraft]
    generator: str
    prompt_version: str
    # Model, request id, and token usage, for cost accounting.
    generation: dict[str, Any] | None = None


class Copywriter(Protocol):
    name: str

    async def write(self, brief: BriefInput) -> CopyBatch: ...


CTA_BY_PLATFORM = {
    "tiktok": "Tap the product link to see the listing.",
    "facebook": "Tap the link to see the listing.",
    "instagram": "The listing link is in my bio.",
    "youtube_shorts": "The listing link is in the description.",
}


class TemplateCopywriter:
    """Deterministic copy built only from the brief: no model call and no invented facts."""

    name = "template"

    async def write(self, brief: BriefInput) -> CopyBatch:
        product = brief.product_name.lower()
        facts = list(brief.verified_facts)
        bullets = "\n".join(f"• {fact}" for fact in facts[:4])
        details = "Check the listing for the current price and full details."
        audience = _lower_first(brief.audience)
        cta = CTA_BY_PLATFORM.get(brief.platform, CTA_BY_PLATFORM["facebook"])
        hashtags = [_hashtag(brief.product_name), _hashtag(brief.category)]
        drafts = [
            CopyDraft(
                "problem",
                brief.angle,
                f"Made for {audience}. From the listing:\n{bullets}\n\n{details}",
                cta,
                hashtags,
            ),
            CopyDraft(
                "benefit",
                f"Why this {product} caught my eye: {facts[0]}" if facts else brief.angle,
                f"Here's what the listing says:\n{bullets}\n\n{details}",
                cta,
                hashtags,
            ),
            CopyDraft(
                "curiosity",
                f"Thinking of getting {_article(product)} {product}? Here's what this one offers.",
                f"A quick look at this {product}:\n{bullets}\n\n{details}",
                cta,
                hashtags,
            ),
        ]
        return CopyBatch(drafts=drafts, generator=self.name, prompt_version=TEMPLATE_VERSION)


class _Variant(BaseModel):
    hook_type: Literal["problem", "benefit", "curiosity"]
    hook: str = Field(min_length=1, max_length=400)
    caption: str = Field(min_length=1, max_length=3000)
    cta: str = Field(min_length=1, max_length=300)
    hashtags: list[str] = Field(default_factory=list, max_length=10)


class _CopyOutput(BaseModel):
    variants: list[_Variant] = Field(min_length=1, max_length=6)


class ClaudeCopywriter:
    def __init__(self, model: str, api_key: str | None = None, client: Any | None = None) -> None:
        self.model = model
        self.name = f"claude:{model}"
        self.client = client or anthropic.AsyncAnthropic(
            api_key=api_key, timeout=120.0, max_retries=2
        )

    async def write(self, brief: BriefInput) -> CopyBatch:
        try:
            response = await self.client.beta.messages.create(
                model=self.model,
                max_tokens=16000,
                # On a policy decline, the API retries on a fallback model in the same call.
                betas=["server-side-fallback-2026-07-01"],
                fallbacks="default",
                output_config={
                    "effort": "medium",
                    "format": {"type": "json_schema", "schema": COPY_SCHEMA},
                },
                system=SYSTEM_PROMPT,
                messages=[{"role": "user", "content": render_brief(_brief_payload(brief))}],
            )
        except anthropic.APIStatusError as error:
            raise UpstreamError(f"The copy model returned HTTP {error.status_code}") from error
        except anthropic.APIConnectionError as error:
            raise UpstreamError("Could not reach the copy model") from error

        if response.stop_reason == "refusal":
            raise UpstreamError("The copy model declined this brief")
        if response.stop_reason == "max_tokens":
            raise UpstreamError("The copy model's answer was cut off")
        text = next((block.text for block in response.content if block.type == "text"), None)
        if text is None:
            raise UpstreamError("The copy model returned no text")
        try:
            output = _CopyOutput.model_validate_json(text)
        except ValidationError as error:
            raise UpstreamError("The copy model returned invalid output") from error

        drafts = [
            CopyDraft(item.hook_type, item.hook, item.caption, item.cta, item.hashtags)
            for item in output.variants[:VARIANTS_PER_BRIEF]
        ]
        return CopyBatch(
            drafts=drafts,
            generator=self.name,
            prompt_version=COPY_PROMPT_VERSION,
            generation={
                "model": response.model,
                "request_id": getattr(response, "_request_id", None),
                "input_tokens": response.usage.input_tokens,
                "output_tokens": response.usage.output_tokens,
            },
        )


def build_copywriter(settings: Settings) -> Copywriter:
    if settings.anthropic_api_key is None:
        return TemplateCopywriter()
    return ClaudeCopywriter(settings.copy_model, settings.anthropic_api_key.get_secret_value())


def copywriter_name(settings: Settings) -> str:
    """Which copywriter will run, without constructing an API client."""
    return "template" if settings.anthropic_api_key is None else f"claude:{settings.copy_model}"


def _brief_payload(brief: BriefInput) -> dict[str, Any]:
    payload = asdict(brief)
    payload["do_not_claim"] = payload.pop("forbidden_claims")
    return payload


def _hashtag(text: str) -> str:
    return "#" + "".join(word[:1].upper() + word[1:] for word in re.findall(r"[A-Za-z0-9]+", text))


def _article(noun: str) -> str:
    return "an" if noun[:1].lower() in "aeiou" else "a"


def _lower_first(text: str) -> str:
    return text[:1].lower() + text[1:]
