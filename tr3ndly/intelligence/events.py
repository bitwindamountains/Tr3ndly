from dataclasses import dataclass
from datetime import datetime

from tr3ndly.db.models import Sensitivity


@dataclass(frozen=True)
class DetectedEvent:
    """What a detector reports. The pipeline turns it into an event cluster and opportunities."""

    dedupe_key: str
    event_type: str
    location: str
    title: str
    summary: str
    consumer_needs: tuple[str, ...]
    sensitivity: Sensitivity
    starts_at: datetime
    expires_at: datetime
    # Timely-score dimensions, 0-100. Freshness is detector-specific: a forecast loses value
    # with each day out, while a calendar date is certain and worth preparing for early.
    freshness: int
    need_strength: int
    actionability: int
    reach: int
    lead_days: int
    signal_external_ids: tuple[str, ...]
    uncertainties: tuple[str, ...]
    rule_version: str
