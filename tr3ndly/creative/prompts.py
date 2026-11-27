"""Versioned prompt and output schema for AI copy variants.

Purpose: turn an approved creative brief into three short social-post copy variants.
Owner: Tr3ndly operator.
Failure behaviour: refusals, truncation, and invalid output raise UpstreamError; nothing is
stored, and the operator can retry or use the template copywriter.
Evaluation: `scripts/eval_copy.py` runs the fixture briefs through the configured copywriter
and reports the policy pass rate. Record results in docs/dev-notes/PROGRESS.md before changing
the version.

Changelog:
- copy-v1 (2026-10-08): first version.
"""

import json
from typing import Any

COPY_PROMPT_VERSION = "copy-v1"

SYSTEM_PROMPT = """\
You write short social-media copy for a Philippine affiliate creator. Each post promotes one \
specific marketplace listing, and viewers buy through the creator's affiliate link. The copy \
must be truthful, because unsupported claims can get posts removed and mislead buyers.

Write three variants, one for each hook type:
- problem: opens with the everyday situation the product helps with.
- benefit: opens with one concrete feature from the verified facts.
- curiosity: opens with a question that makes people want to see the listing.

Rules for every variant:
- Any product feature, spec, or number must come from the verified facts, worded so it stays \
accurate. If a fact is not listed, do not state it.
- No prices, discounts, vouchers, or shipping promises; prices change, so point people to the \
listing.
- No superlatives such as "best", "#1", or "pinaka-", and no urgency or scarcity.
- No health, medical, safety, or guarantee claims, and no fear or disaster framing, even when \
the occasion is weather.
- Do not claim the creator owns or has used the product.
- Do not add an affiliate disclosure; it is appended separately.
- Avoid everything listed under "Do not claim".
- Write natural, conversational English for Filipino audiences. Light Taglish is fine where it \
sounds natural.
- Hook: one line, under 120 characters. Caption: under 600 characters. CTA: one short sentence \
pointing to the link. Hashtags: 0 to 4, without brand names you were not given.
"""

COPY_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "variants": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "hook_type": {"type": "string", "enum": ["problem", "benefit", "curiosity"]},
                    "hook": {"type": "string"},
                    "caption": {"type": "string"},
                    "cta": {"type": "string"},
                    "hashtags": {"type": "array", "items": {"type": "string"}},
                },
                "required": ["hook_type", "hook", "caption", "cta", "hashtags"],
                "additionalProperties": False,
            },
        }
    },
    "required": ["variants"],
    "additionalProperties": False,
}


def render_brief(brief: dict[str, Any]) -> str:
    """The user message: the brief as labelled JSON, so every field is unambiguous."""
    return "Write the three variants for this brief.\n\n" + json.dumps(
        brief, ensure_ascii=False, indent=2
    )
