from __future__ import annotations


def additive_increase(cwnd_mbits: float, rtt_ms: float) -> float:
    return cwnd_mbits + max(0.5, 1460.0 * 8.0 / 1_000_000.0 * (100.0 / max(rtt_ms, 1.0)))


def multiplicative_decrease(cwnd_mbits: float, beta: float = 0.5) -> float:
    return max(1.0, cwnd_mbits * beta)

