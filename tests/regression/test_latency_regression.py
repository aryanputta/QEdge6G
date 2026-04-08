from __future__ import annotations

from src.simulation.scenario_runner import run_scenario


def test_greedy_latency_regression(config):
    rows, _ = run_scenario(config, solver_name="greedy", steps=2)
    p95 = sum(float(row["p95_latency_ms"]) for row in rows) / len(rows)
    assert 10.0 < p95 < 80.0

