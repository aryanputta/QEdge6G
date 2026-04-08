from __future__ import annotations

from src.benchmarks.benchmark_config import load_scenario_config
from src.simulation.scenario_runner import run_scenario


def test_bursty_traffic_solver_smoke():
    config = load_scenario_config("configs/base.yaml", "configs/simulation/tcp_bursty.yaml")
    config["traffic"]["num_users"] = 6
    rows, _ = run_scenario(config, solver_name="simulated_annealing", steps=2)
    assert max(float(row["goodput_mbps"]) for row in rows) > 0.0

