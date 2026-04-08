from __future__ import annotations

from src.transport.queue_model import FluidQueue


def test_queue_delay_and_loss_increase_under_overload():
    queue = FluidQueue(service_rate_mbps=50.0, buffer_mbits=20.0)
    snapshot = queue.step(arrivals_mbits=120.0)
    assert snapshot.delay_ms > 0.0
    assert snapshot.loss_rate > 0.0

