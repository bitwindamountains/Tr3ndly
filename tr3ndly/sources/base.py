import asyncio
import hashlib
import json
import random
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Protocol

import httpx


@dataclass(frozen=True)
class SourceDefinition:
    """Registry facts recorded for every source (plan section 10)."""

    slug: str
    display_name: str
    access_method: str
    terms_url: str | None
    attribution: str
    poll_interval: timedelta
    source_confidence: int


@dataclass(frozen=True)
class NormalizedSignal:
    external_id: str
    title: str
    summary: str
    observed_at: datetime
    canonical_url: str | None = None
    # Structured facts that the source licence allows us to retain.
    facts: dict[str, Any] = field(default_factory=dict)

    @property
    def content_hash(self) -> str:
        body = json.dumps(
            {"external_id": self.external_id, "facts": self.facts},
            sort_keys=True,
            separators=(",", ":"),
            default=str,
        )
        return hashlib.sha256(body.encode()).hexdigest()


class SourceAdapter(Protocol):
    definition: SourceDefinition

    async def fetch(self, client: httpx.AsyncClient) -> list[Any]:
        """Return raw provider items. No AI and no persistence inside adapters."""
        ...

    def normalize(self, item: Any, fetched_at: datetime) -> list[NormalizedSignal]: ...


async def with_retries[T](
    operation: Callable[[], Awaitable[T]],
    attempts: int = 3,
    base_delay: float = 1.0,
) -> T:
    """Retry transient HTTP failures with exponential backoff and jitter."""
    for attempt in range(1, attempts + 1):
        try:
            return await operation()
        except (httpx.TransportError, httpx.HTTPStatusError) as error:
            retryable = not isinstance(error, httpx.HTTPStatusError) or (
                error.response.status_code == 429 or error.response.status_code >= 500
            )
            if not retryable or attempt == attempts:
                raise
            await asyncio.sleep(base_delay * 2 ** (attempt - 1) + random.uniform(0, base_delay))
    raise AssertionError("unreachable")
