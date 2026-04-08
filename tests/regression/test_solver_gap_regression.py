from __future__ import annotations

from src.simulation.scenario_runner import run_scenario


def test_exact_objective_beats_greedy(config):
    greedy_rows, _ = run_scenario(config, solver_name="greedy", steps=1)
    exact_rows, _ = run_scenario(config, solver_name="exact", steps=1)
    assert float(exact_rows[0]["objective_value"]) <= float(greedy_rows[0]["objective_value"])

