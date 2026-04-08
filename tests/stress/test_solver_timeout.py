from __future__ import annotations

from src.benchmarks.benchmark_config import load_scenario_config
from src.simulation.scenario_runner import run_scenario


def test_quantum_inspired_runtime_smoke():
    config = load_scenario_config("configs/base.yaml", "configs/simulation/wireless_dense.yaml")
    config["traffic"]["num_users"] = 6
    rows, _ = run_scenario(config, solver_name="quantum_inspired", steps=1)
    assert float(rows[0]["solver_runtime_s"]) < 5.0

