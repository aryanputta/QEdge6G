from __future__ import annotations

from src.benchmarks.benchmark_config import load_scenario_config
from src.simulation.scenario_runner import run_scenario


def test_quantum_inspired_tail_latency_not_worse_than_greedy_in_dense_smoke():
    config = load_scenario_config("configs/base.yaml", "configs/simulation/wireless_dense.yaml")
    config["traffic"]["num_users"] = 6
    greedy_rows, _ = run_scenario(config, solver_name="greedy", steps=2)
    quantum_rows, _ = run_scenario(config, solver_name="quantum_inspired", steps=2)
    greedy_p95 = sum(float(row["p95_latency_ms"]) for row in greedy_rows) / len(greedy_rows)
    quantum_p95 = sum(float(row["p95_latency_ms"]) for row in quantum_rows) / len(quantum_rows)
    assert quantum_p95 <= greedy_p95 * 1.1

