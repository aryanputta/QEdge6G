from __future__ import annotations

from src.benchmarks.benchmark_config import load_scenario_config
from src.simulation.scenario_runner import run_scenario


def test_transport_and_edge_interaction_show_queue_delay():
    config = load_scenario_config("configs/base.yaml", "configs/simulation/edge_overload.yaml")
    config["traffic"]["num_users"] = 5
    rows, _ = run_scenario(config, solver_name="greedy", steps=2)
    assert max(float(row["queue_delay_ms"]) for row in rows) > 0.0

