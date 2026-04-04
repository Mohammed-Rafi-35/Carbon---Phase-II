from __future__ import annotations

from dataclasses import dataclass


@dataclass
class MetricsSnapshot:
    sent_count: int
    failed_count: int
    retry_count: int
    queue_depth: int


class MetricsService:
    def __init__(self) -> None:
        self.sent_count = 0
        self.failed_count = 0
        self.retry_count = 0
        self.queue_depth = 0

    def queued(self) -> None:
        self.queue_depth += 1

    def dequeued(self) -> None:
        if self.queue_depth > 0:
            self.queue_depth -= 1

    def sent(self) -> None:
        self.sent_count += 1

    def failed(self) -> None:
        self.failed_count += 1

    def retried(self) -> None:
        self.retry_count += 1

    def snapshot(self) -> MetricsSnapshot:
        return MetricsSnapshot(
            sent_count=self.sent_count,
            failed_count=self.failed_count,
            retry_count=self.retry_count,
            queue_depth=self.queue_depth,
        )


metrics_service = MetricsService()
