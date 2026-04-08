from __future__ import annotations

from src.benchmarks.benchmark_config import load_scenario_config
from src.simulation.scenario_runner import run_scenario


def test_dense_topology_smoke():
    config = load_scenario_config("configs/base.yaml", "configs/simulation/wireless_dense.yaml")
    config["traffic"]["num_users"] = 10
    rows, _ = run_scenario(config, solver_name="greedy", steps=2)
    assert len(rows) == 2

