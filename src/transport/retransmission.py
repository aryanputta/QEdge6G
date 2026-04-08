from __future__ import annotations


def retransmission_penalty_ms(loss_rate: float, rtt_ms: float, transport_factor: float = 1.0) -> float:
    return loss_rate * rtt_ms * 4.0 * transport_factor

