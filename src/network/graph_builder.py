from __future__ import annotations

import networkx as nx

from src.network.topology import TopologySnapshot


def copy_graph_with_link_weights(topology: TopologySnapshot, link_overrides: dict[str, float] | None = None) -> nx.Graph:
    graph = topology.graph.copy()
    if link_overrides:
        for _, _, data in graph.edges(data=True):
            link_id = data["link_id"]
            if link_id in link_overrides:
                data["weight"] = link_overrides[link_id]
    return graph

