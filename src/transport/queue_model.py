from __future__ import annotations

from dataclasses import dataclass


@dataclass
class QueueSnapshot:
    backlog_mbits: float
    served_mbits: float
    dropped_mbits: float
    delay_ms: float
    utilization: float
    loss_rate: float


class FluidQueue:
    def __init__(self, service_rate_mbps: float, buffer_mbits: float) -> None:
        self.service_rate_mbps = max(0.1, service_rate_mbps)
        self.buffer_mbits = max(1.0, buffer_mbits)
        self.backlog_mbits = 0.0
        self.delay_ms = 0.0
        self.utilization = 0.0
        self.loss_rate = 0.0

    def step(self, arrivals_mbits: float, dt_s: float = 1.0) -> QueueSnapshot:
        service_budget = self.service_rate_mbps * dt_s
        total = self.backlog_mbits + max(0.0, arrivals_mbits)
        served = min(total, service_budget)
        backlog = max(0.0, total - served)
        dropped = max(0.0, backlog - self.buffer_mbits)
        backlog -= dropped

        self.backlog_mbits = backlog
        self.delay_ms = 25.0 * self.backlog_mbits / self.service_rate_mbps
        self.utilization = min(1.0, total / max(service_budget, 1e-6))
        self.loss_rate = 0.0 if arrivals_mbits <= 0 else min(1.0, dropped / arrivals_mbits)
        return QueueSnapshot(
            backlog_mbits=self.backlog_mbits,
            served_mbits=served,
            dropped_mbits=dropped,
            delay_ms=self.delay_ms,
            utilization=self.utilization,
            loss_rate=self.loss_rate,
        )
