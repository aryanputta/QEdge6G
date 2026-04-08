from __future__ import annotations

from src.simulation.scenario_runner import run_scenario


def test_end_to_end_simulation_runs(config):
    rows, summary = run_scenario(config, solver_name="greedy", steps=2)
    assert len(rows) == 2
    assert summary["throughput_mbps"] > 0.0

