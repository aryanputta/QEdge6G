from __future__ import annotations

from src.solvers.ilp_solver import solve as solve_exact


def test_exact_solver_satisfies_capacity_constraints(optimization_instance):
    _, _, _, _, _, instance = optimization_instance
    result = solve_exact(instance)
    assert result.violations == []

