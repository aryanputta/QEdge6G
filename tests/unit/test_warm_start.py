from __future__ import annotations

from src.solvers.greedy_solver import solve as solve_greedy
from src.solvers.quantum_inspired_solver import solve as solve_quantum


def test_quantum_solver_accepts_warm_start(optimization_instance):
    _, _, _, _, _, instance = optimization_instance
    greedy = solve_greedy(instance)
    warm_ids = [decision.option_id for decision in greedy.decisions]
    result = solve_quantum(instance, steps=60, initial_option_ids=warm_ids)
    assert result.metadata["warm_start"] is True
