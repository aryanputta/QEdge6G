from __future__ import annotations

from src.transport.queue_model import FluidQueue
from src.utils.models import Link


def effective_link_capacity(link: Link) -> float:
    return max(1.0, link.capacity_mbps * link.degraded_factor)


def link_snapshot(link: Link, queue: FluidQueue) -> dict[str, float]:
    return {
        "capacity_mbps": effective_link_capacity(link),
        "latency_ms": link.latency_ms + queue.delay_ms,
        "queue_delay_ms": queue.delay_ms,
        "loss_rate": min(1.0, link.loss_rate + queue.loss_rate),
        "utilization": queue.utilization,
    }

