"""Evaluate the copywriter against the fixture briefs.

Runs every brief in tests/fixtures/copy_briefs.json through the configured copywriter (Claude
when ANTHROPIC_API_KEY is set, the template otherwise) and reports how many variants pass the
policy checks. Run it before changing COPY_PROMPT_VERSION, and record the result in PROGRESS.md.
Each Claude run makes one API call per brief.

    .venv\\Scripts\\python.exe scripts\\eval_copy.py
    .venv\\Scripts\\python.exe scripts\\eval_copy.py --template   # force the template
"""

import argparse
import asyncio
import json
from collections import Counter
from pathlib import Path

from tr3ndly.config import get_settings
from tr3ndly.creative.copywriter import (
    BriefInput,
    Copywriter,
    TemplateCopywriter,
    build_copywriter,
)
from tr3ndly.creative.policy import POLICY_VERSION, check_copy, has_blocking

FIXTURES = Path(__file__).resolve().parents[1] / "tests" / "fixtures" / "copy_briefs.json"


async def evaluate(copywriter: Copywriter) -> int:
    briefs = json.loads(FIXTURES.read_text(encoding="utf-8"))
    total = passed = 0
    codes: Counter[str] = Counter()
    tokens = Counter[str]()
    for item in briefs:
        brief = BriefInput(
            **{
                **item,
                "verified_facts": tuple(item["verified_facts"]),
                "forbidden_claims": tuple(item["forbidden_claims"]),
            }
        )
        batch = await copywriter.write(brief)
        if batch.generation:
            tokens["input"] += batch.generation.get("input_tokens") or 0
            tokens["output"] += batch.generation.get("output_tokens") or 0
        for draft in batch.drafts:
            issues = check_copy(
                hook=draft.hook,
                caption=draft.caption,
                cta=draft.cta,
                hashtags=draft.hashtags,
                verified_facts=list(brief.verified_facts),
            )
            total += 1
            if not has_blocking(issues):
                passed += 1
            codes.update(issue["code"] for issue in issues)
            print(f"\n[{brief.product_name} / {draft.hook_type}] {draft.hook}")
            for issue in issues:
                print(f"  - {issue['code']}: {issue['match']!r} in {issue['field']}")

    print(f"\ncopywriter: {copywriter.name}  policy: {POLICY_VERSION}")
    print(f"variants passing policy: {passed}/{total}")
    if codes:
        print("issues:", dict(codes.most_common()))
    if tokens:
        print(f"tokens: {tokens['input']} in, {tokens['output']} out")
    return 0 if passed == total else 1


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--template", action="store_true", help="use the template copywriter")
    args = parser.parse_args()
    copywriter = TemplateCopywriter() if args.template else build_copywriter(get_settings())
    return asyncio.run(evaluate(copywriter))


if __name__ == "__main__":
    raise SystemExit(main())
