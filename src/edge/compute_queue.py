from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ComputeSnapshot:
    backlog_units: float
    served_units: float
    dropped_units: float
    delay_ms: float
    utilization: float


class ComputeQueue:
    def __init__(self, service_rate_units: float, buffer_units: float) -> None:
        self.service_rate_units = max(0.1, service_rate_units)
        self.buffer_units = max(1.0, buffer_units)
        self.backlog_units = 0.0
        self.delay_ms = 0.0
        self.utilization = 0.0

    def step(self, arrivals_units: float, dt_s: float = 1.0) -> ComputeSnapshot:
        service_budget = self.service_rate_units * dt_s
        total = self.backlog_units + max(0.0, arrivals_units)
        served = min(total, service_budget)
        backlog = max(0.0, total - served)
        dropped = max(0.0, backlog - self.buffer_units)
        backlog -= dropped
        self.backlog_units = backlog
        self.delay_ms = 25.0 * self.backlog_units / self.service_rate_units
        self.utilization = min(1.0, total / max(service_budget, 1e-6))
        return ComputeSnapshot(
            backlog_units=self.backlog_units,
            served_units=served,
            dropped_units=dropped,
            delay_ms=self.delay_ms,
            utilization=self.utilization,
        )
