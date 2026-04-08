from __future__ import annotations

import matplotlib.pyplot as plt
import networkx as nx


def plot_topology(topology, output_path: str) -> None:
    positions = nx.get_node_attributes(topology.graph, "pos")
    colors = []
    for _, data in topology.graph.nodes(data=True):
        kind = data["kind"]
        colors.append({"base_station": "#1f77b4", "aggregation": "#ff7f0e", "edge": "#2ca02c"}[kind])
    plt.figure(figsize=(6, 6))
    nx.draw(topology.graph, positions, node_color=colors, with_labels=True, node_size=800, font_size=8)
    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()

