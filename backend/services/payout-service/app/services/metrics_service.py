from __future__ import annotations

from prometheus_client import Counter, Histogram


PAYOUT_SUCCESS_TOTAL = Counter("payout_success_total", "Number of successfully processed payouts")
PAYOUT_FAILURE_TOTAL = Counter("payout_failure_total", "Number of failed payout attempts")
PAYOUT_RETRY_TOTAL = Counter("payout_retry_total", "Number of retry attempts")
PAYOUT_PROCESSING_SECONDS = Histogram("payout_processing_seconds", "Payout processing latency in seconds")
