from __future__ import annotations

from dataclasses import dataclass, field

from src.edge.compute_queue import ComputeQueue
from src.transport.quic_model import QUICFlowState
from src.transport.queue_model import FluidQueue
from src.transport.tcp_model import TCPFlowState


@dataclass
class StateTracker:
    link_queues: dict[str, FluidQueue]
    edge_queues: dict[str, ComputeQueue]
    tcp_flows: dict[str, TCPFlowState] = field(default_factory=dict)
    quic_flows: dict[str, QUICFlowState] = field(default_factory=dict)
    history: list[dict] = field(default_factory=list)


def initialize_state(topology) -> StateTracker:
    return StateTracker(
        link_queues={
            link_id: FluidQueue(service_rate_mbps=link.capacity_mbps, buffer_mbits=link.buffer_mbits)
            for link_id, link in topology.links.items()
        },
        edge_queues={
            edge_id: ComputeQueue(service_rate_units=server.service_rate_units, buffer_units=server.queue_buffer_units)
            for edge_id, server in topology.edges.items()
        },
    )

