from __future__ import annotations

from src.solvers.quantum_inspired_solver import solve as solve_quantum_inspired


def test_solver_pipeline_returns_one_decision_per_user(optimization_instance):
    _, _, _, _, _, instance = optimization_instance
    result = solve_quantum_inspired(instance, steps=120)
    assert len(result.decisions) == len(instance.users)
    assert all(decision.user_id in instance.users for decision in result.decisions)

