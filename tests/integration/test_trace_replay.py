from __future__ import annotations

from src.benchmarks.benchmark_config import load_scenario_config
from src.simulation.scenario_runner import run_scenario


def test_trace_replay_scenario_runs():
    config = load_scenario_config("configs/base.yaml", "configs/simulation/trace_replay.yaml")
    rows, _ = run_scenario(config, solver_name="quantum_inspired", steps=3)
    assert len(rows) == 3
    assert all(float(row["throughput_mbps"]) > 0.0 for row in rows)

