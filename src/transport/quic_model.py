from __future__ import annotations

from dataclasses import dataclass

from src.transport.retransmission import retransmission_penalty_ms


@dataclass
class QUICFlowState:
    pacing_rate_mbps: float = 12.0
    cwnd_mbits: float = 14.0
    min_rtt_ms: float = 18.0
    pacing_gain: float = 1.0
    delivery_rate_mbps: float = 12.0
    rtt_ms: float = 18.0


def step_quic_flow(
    state: QUICFlowState,
    demand_mbps: float,
    path_capacity_mbps: float,
    rtt_ms: float,
    loss_rate: float,
) -> tuple[float, float, float]:
    state.rtt_ms = max(1.0, rtt_ms)
    state.min_rtt_ms = min(state.min_rtt_ms, state.rtt_ms)
    bdp_mbits = max(1.0, path_capacity_mbps * state.rtt_ms / 1000.0)
    if loss_rate > 0.02:
        state.pacing_gain = 0.82
        state.cwnd_mbits = max(2.0, state.cwnd_mbits * 0.82)
    else:
        state.pacing_gain = min(1.25, state.pacing_gain + 0.04)
        state.cwnd_mbits = min(2.2 * bdp_mbits, state.cwnd_mbits + 0.9)
    pacing_target = state.pacing_gain * max(state.delivery_rate_mbps, path_capacity_mbps * 0.6)
    cwnd_limited_rate = state.cwnd_mbits * 1000.0 / state.rtt_ms
    state.pacing_rate_mbps = max(1.0, 0.55 * state.pacing_rate_mbps + 0.45 * pacing_target)
    queue_inflation = max(0.0, (state.rtt_ms - state.min_rtt_ms) / max(state.min_rtt_ms, 1.0))
    send_rate = min(demand_mbps, path_capacity_mbps, state.pacing_rate_mbps, cwnd_limited_rate)
    goodput = send_rate * (1.0 - min(0.45, loss_rate * 0.65)) * max(0.8, 1.0 - 0.12 * queue_inflation)
    penalty = retransmission_penalty_ms(loss_rate, rtt_ms, transport_factor=0.45 + 0.4 * queue_inflation)
    state.delivery_rate_mbps = 0.75 * state.delivery_rate_mbps + 0.25 * goodput
    return send_rate, goodput, penalty
