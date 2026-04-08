from __future__ import annotations

from src.transport.tcp_model import TCPFlowState, step_tcp_flow


def test_tcp_cwnd_increases_without_loss():
    state = TCPFlowState(cwnd_mbits=10.0, rtt_ms=20.0)
    result = step_tcp_flow(state, demand_mbps=40.0, path_capacity_mbps=100.0, rtt_ms=20.0, loss_rate=0.0)
    assert result.cwnd_mbits > 10.0
    assert result.goodput_mbps <= result.send_rate_mbps


def test_tcp_cwnd_decreases_on_loss():
    state = TCPFlowState(cwnd_mbits=12.0, rtt_ms=20.0)
    result = step_tcp_flow(state, demand_mbps=40.0, path_capacity_mbps=100.0, rtt_ms=20.0, loss_rate=0.05)
    assert result.cwnd_mbits < 12.0

