from __future__ import annotations

import pytest

from src.simulation.scenario_runner import run_scenario

def test_exact_objective_beats_greedy(config):
    greedy_rows, _ = run_scenario(config, solver_name="greedy", steps=1)
    exact_rows, _ = run_scenario(config, solver_name="exact", steps=1)
    
    exact_obj = float(exact_rows[0]["objective_value"])
    greedy_obj = float(greedy_rows[0]["objective_value"])
    
    # Use approximate equality to handle floating-point precision
    assert exact_obj == pytest.approx(greedy_obj, abs=1e-9) or exact_obj < greedy_obj
