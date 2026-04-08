from __future__ import annotations

from dataclasses import dataclass

import networkx as nx
import numpy as np

from src.utils.models import BaseStation, EdgeServer, Link


@dataclass
class TopologySnapshot:
    graph: nx.Graph
    base_stations: dict[str, BaseStation]
    edges: dict[str, EdgeServer]
    links: dict[str, Link]
    transport_nodes: list[str]


def build_topology(config: dict, rng: np.random.Generator) -> TopologySnapshot:
    graph = nx.Graph()
    topology_cfg = config["topology"]
    edge_cfg = config["edge"]
    num_bs = topology_cfg["num_base_stations"]
    num_edges = topology_cfg["num_edges"]
    num_aggs = topology_cfg.get("num_aggregation_nodes", 2)
    area_km = topology_cfg.get("area_km", 2.0)

    base_stations: dict[str, BaseStation] = {}
    edges: dict[str, EdgeServer] = {}
    links: dict[str, Link] = {}
    transport_nodes: list[str] = []

    bs_x = np.linspace(0.15, area_km - 0.15, num_bs)
    for index in range(num_bs):
        bs_id = f"bs{index}"
        station = BaseStation(
            bs_id=bs_id,
            x=float(bs_x[index]),
            y=float(rng.uniform(0.1, area_km - 0.1)),
            spectrum_mhz=int(topology_cfg.get("base_station_spectrum_mhz", 100)),
            rb_budget=int(topology_cfg.get("rb_budget", 100)),
        )
        base_stations[bs_id] = station
        graph.add_node(bs_id, kind="base_station", pos=(station.x, station.y))

    agg_x = np.linspace(0.3, area_km - 0.3, num_aggs)
    for index in range(num_aggs):
        agg_id = f"agg{index}"
        transport_nodes.append(agg_id)
        graph.add_node(agg_id, kind="aggregation", pos=(float(agg_x[index]), area_km / 2.0))

    edge_x = np.linspace(0.2, area_km - 0.2, num_edges)
    edge_caps = edge_cfg.get("capacity_units", [24, 20, 28])
    if not isinstance(edge_caps, list):
        edge_caps = [int(edge_caps)] * num_edges
    service_rates = edge_cfg.get("service_rate_units", [18, 16, 20])
    if not isinstance(service_rates, list):
        service_rates = [int(service_rates)] * num_edges

    for index in range(num_edges):
        edge_id = f"edge{index}"
        agg_id = transport_nodes[index % len(transport_nodes)]
        server = EdgeServer(
            edge_id=edge_id,
            attached_agg=agg_id,
            x=float(edge_x[index]),
            y=float(area_km - 0.15),
            capacity_units=int(edge_caps[index % len(edge_caps)]),
            service_rate_units=int(service_rates[index % len(service_rates)]),
            queue_buffer_units=int(edge_cfg.get("queue_buffer_units", 64)),
            energy_cost=float(edge_cfg.get("energy_cost", 1.0)),
        )
        edges[edge_id] = server
        graph.add_node(edge_id, kind="edge", pos=(server.x, server.y))

    def add_link(src: str, dst: str, capacity_mbps: int, latency_ms: float, buffer_mbits: int) -> None:
        link_id = f"{src}::{dst}"
        link = Link(
            link_id=link_id,
            src=src,
            dst=dst,
            capacity_mbps=capacity_mbps,
            latency_ms=latency_ms,
            buffer_mbits=buffer_mbits,
        )
        links[link_id] = link
        graph.add_edge(src, dst, weight=latency_ms, link_id=link_id)

    base_capacity = int(topology_cfg.get("backhaul_capacity_mbps", 160))
    base_buffer = int(topology_cfg.get("backhaul_buffer_mbits", 240))
    latency_range = topology_cfg.get("backhaul_latency_ms", [2.0, 7.0])

    for station in base_stations.values():
        for agg_id in transport_nodes:
            capacity = max(20, int(base_capacity * rng.uniform(0.7, 1.1)))
            latency = float(rng.uniform(latency_range[0], latency_range[1]))
            add_link(station.bs_id, agg_id, capacity, latency, base_buffer)

    for source in transport_nodes:
        for target in transport_nodes:
            if source >= target:
                continue
            capacity = max(20, int(base_capacity * rng.uniform(0.55, 0.95)))
            latency = float(rng.uniform(latency_range[0], latency_range[1] + 2.0))
            add_link(source, target, capacity, latency, base_buffer)

    for server in edges.values():
        for agg_id in transport_nodes:
            capacity = max(20, int(base_capacity * rng.uniform(0.8, 1.2)))
            latency = float(rng.uniform(1.0, latency_range[1]))
            add_link(agg_id, server.edge_id, capacity, latency, base_buffer)

    if topology_cfg.get("edge_relay_links", True):
        edge_ids = list(edges)
        for left, right in zip(edge_ids, edge_ids[1:]):
            add_link(left, right, max(20, int(base_capacity * 0.65)), float(rng.uniform(1.0, 4.0)), base_buffer)

    return TopologySnapshot(
        graph=graph,
        base_stations=base_stations,
        edges=edges,
        links=links,
        transport_nodes=transport_nodes,
    )

