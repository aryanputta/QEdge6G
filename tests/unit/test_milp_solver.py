from __future__ import annotations

from src.solvers.ilp_solver import solve as solve_exact


def test_milp_solver_uses_external_backend_when_available(optimization_instance):
    _, _, _, _, _, instance = optimization_instance
    result = solve_exact(instance)
    assert result.metadata["backend"] in {"scipy_milp", "branch_and_bound_fallback"}
    assert result.violations == []

