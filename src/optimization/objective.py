from __future__ import annotations

from src.edge.edge_server import compute_service_time_ms
from src.edge.placement_cost import placement_cost
from src.transport.retransmission import retransmission_penalty_ms
from src.utils.models import EdgeServer, PathState, UserState


def estimate_latency_ms(
    user: UserState,
    path: PathState,
    server: EdgeServer,
    allocated_mbps: float,
    radio_capacity_mbps: float,
    edge_queue_delay_ms: float,
) -> float:
    radio_delay = 25.0 * allocated_mbps / max(radio_capacity_mbps, 1.0)
    compute_delay = edge_queue_delay_ms + compute_service_time_ms(server, user.workload.compute_demand_units)
    transport_delay = path.base_latency_ms + path.queue_delay_ms
    retransmit = retransmission_penalty_ms(path.loss_rate, max(5.0, path.base_latency_ms + path.queue_delay_ms))
    return radio_delay + transport_delay + compute_delay + retransmit


def option_cost(
    user: UserState,
    path: PathState,
    server: EdgeServer,
    allocated_mbps: float,
    radio_capacity_mbps: float,
    edge_queue_delay_ms: float,
    tier_utility: float,
    fairness_bias: float,
) -> tuple[float, float, float]:
    latency_ms = estimate_latency_ms(
        user=user,
        path=path,
        server=server,
        allocated_mbps=allocated_mbps,
        radio_capacity_mbps=radio_capacity_mbps,
        edge_queue_delay_ms=edge_queue_delay_ms,
    )
    sla_penalty = max(0.0, latency_ms - user.workload.latency_sla_ms) * 2.0 * user.workload.priority
    loss_penalty = path.loss_rate * 100.0
    compute_penalty = placement_cost(user.workload, server, path.base_latency_ms)
    reward = 14.0 * user.workload.priority * tier_utility + fairness_bias
    total = latency_ms + sla_penalty + loss_penalty + compute_penalty - reward
    return total, latency_ms, max(0.0, allocated_mbps * (1.0 - path.loss_rate))


def drop_cost(user: UserState) -> float:
    return 55.0 * user.workload.priority + user.workload.latency_sla_ms * 0.5
