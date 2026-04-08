from __future__ import annotations

from itertools import islice

import networkx as nx

from src.network.topology import TopologySnapshot
from src.transport.queue_model import FluidQueue
from src.utils.models import PathState


def enumerate_paths(
    topology: TopologySnapshot,
    link_queues: dict[str, FluidQueue],
    k_paths: int = 3,
) -> dict[tuple[str, str], list[PathState]]:
    paths: dict[tuple[str, str], list[PathState]] = {}
    for bs_id in topology.base_stations:
        for edge_id in topology.edges:
            candidates = []
            simple_paths = nx.shortest_simple_paths(topology.graph, bs_id, edge_id, weight="weight")
            for index, nodes in enumerate(islice(simple_paths, k_paths)):
                link_ids: list[str] = []
                capacity = None
                base_latency = 0.0
                queue_delay = 0.0
                loss_rate = 0.0
                utilization = 0.0
                for src, dst in zip(nodes, nodes[1:]):
                    link_id = topology.graph.edges[src, dst]["link_id"]
                    link_ids.append(link_id)
                    link = topology.links[link_id]
                    queue = link_queues[link_id]
                    effective_capacity = int(link.capacity_mbps * link.degraded_factor)
                    capacity = effective_capacity if capacity is None else min(capacity, effective_capacity)
                    base_latency += link.latency_ms
                    queue_delay += queue.delay_ms
                    loss_rate = max(loss_rate, queue.loss_rate + link.loss_rate)
                    utilization = max(utilization, queue.utilization)
                candidates.append(
                    PathState(
                        path_id=f"{bs_id}->{edge_id}:p{index}",
                        bs_id=bs_id,
                        edge_id=edge_id,
                        nodes=list(nodes),
                        links=link_ids,
                        base_latency_ms=base_latency,
                        capacity_mbps=int(capacity or 1),
                        utilization=utilization,
                        queue_delay_ms=queue_delay,
                        loss_rate=min(1.0, loss_rate),
                    )
                )
            paths[(bs_id, edge_id)] = candidates
    return paths
