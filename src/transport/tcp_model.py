from __future__ import annotations

from dataclasses import dataclass

from src.transport.congestion_control import additive_increase, multiplicative_decrease
from src.transport.retransmission import retransmission_penalty_ms


@dataclass
class TCPFlowState:
    cwnd_mbits: float = 10.0
    ssthresh_mbits: float = 18.0
    rtt_ms: float = 20.0
    min_rtt_ms: float = 20.0
    delivery_rate_mbps: float = 10.0
    loss_events: int = 0


@dataclass
class TCPResult:
    send_rate_mbps: float
    goodput_mbps: float
    retransmission_penalty_ms: float
    cwnd_mbits: float


def step_tcp_flow(
    state: TCPFlowState,
    demand_mbps: float,
    path_capacity_mbps: float,
    rtt_ms: float,
    loss_rate: float,
) -> TCPResult:
    state.rtt_ms = max(1.0, rtt_ms)
    prior_cwnd = state.cwnd_mbits
    state.min_rtt_ms = min(state.min_rtt_ms, state.rtt_ms)
    bdp_mbits = max(1.0, path_capacity_mbps * state.rtt_ms / 1000.0)
    if loss_rate > 0.02:
        state.ssthresh_mbits = max(2.0, multiplicative_decrease(state.cwnd_mbits, beta=0.65))
        state.cwnd_mbits = state.ssthresh_mbits
        state.loss_events += 1
    else:
        if state.cwnd_mbits < state.ssthresh_mbits:
            state.cwnd_mbits = min(state.ssthresh_mbits * 1.25, state.cwnd_mbits * 1.55)
        else:
            state.cwnd_mbits = additive_increase(state.cwnd_mbits, state.rtt_ms)
    cwnd_cap = max(2.0, 1.8 * bdp_mbits, prior_cwnd * 1.6)
    state.cwnd_mbits = min(max(1.0, state.cwnd_mbits), cwnd_cap)

    cwnd_limited_rate = state.cwnd_mbits * 1000.0 / state.rtt_ms
    queue_inflation = max(0.0, (state.rtt_ms - state.min_rtt_ms) / max(state.min_rtt_ms, 1.0))
    send_rate = min(max(0.0, demand_mbps), path_capacity_mbps, cwnd_limited_rate)
    goodput = send_rate * (1.0 - min(0.95, loss_rate)) * max(0.72, 1.0 - 0.18 * queue_inflation)
    penalty = retransmission_penalty_ms(loss_rate, state.rtt_ms, transport_factor=1.0 + queue_inflation)
    state.delivery_rate_mbps = 0.7 * state.delivery_rate_mbps + 0.3 * goodput
    return TCPResult(
        send_rate_mbps=send_rate,
        goodput_mbps=goodput,
        retransmission_penalty_ms=penalty,
        cwnd_mbits=state.cwnd_mbits,
    )
