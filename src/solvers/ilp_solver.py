from __future__ import annotations

import time

import numpy as np
from scipy.optimize import Bounds, LinearConstraint, milp

from src.optimization.validator import validate_decisions
from src.solvers.common import (
    all_options,
    apply_option,
    empty_usage,
    is_feasible,
    min_remaining_bound,
    objective_from_option_ids,
    option_ids_to_decisions,
)
from src.utils.models import OptimizationInstance, SolverResult


def _solve_with_branch_and_bound(instance: OptimizationInstance) -> tuple[list[str], float]:
    user_order = sorted(
        instance.options_by_user,
        key=lambda user_id: (len(instance.options_by_user[user_id]), -instance.users[user_id].workload.priority),
    )

    best_cost = float("inf")
    best_selection: list[str] = []
    usage = empty_usage(instance)

    def branch(index: int, current_selection: list[str], current_cost: float) -> None:
        nonlocal best_cost, best_selection
        if index == len(user_order):
            if current_cost < best_cost:
                best_cost = current_cost
                best_selection = current_selection.copy()
            return
        remaining_users = user_order[index:]
        bound = current_cost + min_remaining_bound(instance, remaining_users)
        if bound >= best_cost:
            return

        user_id = user_order[index]
        for option in instance.options_by_user[user_id]:
            if not is_feasible(instance, option, usage):
                continue
            apply_option(instance, option, usage)
            current_selection.append(option.option_id)
            branch(index + 1, current_selection, current_cost + option.objective_cost)
            current_selection.pop()
            if option.admitted:
                for name, constraint in instance.capacities.items():
                    usage[name] -= constraint.option_weights.get(option.option_id, 0)

    branch(0, [], 0.0)
    if not best_selection:
        best_selection = [options[-1].option_id for options in instance.options_by_user.values()]
        best_cost = objective_from_option_ids(instance, best_selection)
    return best_selection, best_cost


def _solve_with_scipy_milp(instance: OptimizationInstance) -> tuple[list[str], float]:
    option_lookup = all_options(instance)
    option_ids = list(option_lookup)
    option_index = {option_id: idx for idx, option_id in enumerate(option_ids)}
    c = np.asarray([option_lookup[option_id].objective_cost for option_id in option_ids], dtype=float)

    constraints = []
    for user_id, options in instance.options_by_user.items():
        row = np.zeros(len(option_ids), dtype=float)
        for option in options:
            row[option_index[option.option_id]] = 1.0
        constraints.append(LinearConstraint(row.reshape(1, -1), lb=np.array([1.0]), ub=np.array([1.0])))

    for constraint in instance.capacities.values():
        row = np.zeros(len(option_ids), dtype=float)
        for option_id, weight in constraint.option_weights.items():
            if option_id in option_index:
                row[option_index[option_id]] = float(weight)
        constraints.append(
            LinearConstraint(
                row.reshape(1, -1),
                lb=np.array([-np.inf]),
                ub=np.array([float(constraint.capacity_units)]),
            )
        )

    result = milp(
        c=c,
        integrality=np.ones(len(option_ids), dtype=int),
        bounds=Bounds(lb=np.zeros(len(option_ids)), ub=np.ones(len(option_ids))),
        constraints=constraints,
        options={
            "time_limit": float(instance.metadata.get("milp_time_limit_s", 20.0)),
            "presolve": True,
        },
    )
    if not result.success or result.x is None:
        raise RuntimeError(result.message if hasattr(result, "message") else "scipy milp failed")

    selected = [option_ids[idx] for idx, value in enumerate(result.x) if value > 0.5]
    if len(selected) != len(instance.users):
        raise RuntimeError("scipy milp returned an incomplete selection")
    return selected, float(result.fun)


def solve(instance: OptimizationInstance, initial_option_ids: list[str] | None = None) -> SolverResult:
    del initial_option_ids
    start = time.perf_counter()
    backend = "scipy_milp"
    try:
        selection, objective = _solve_with_scipy_milp(instance)
        solver_name = "milp_exact"
    except Exception:
        backend = "branch_and_bound_fallback"
        selection, objective = _solve_with_branch_and_bound(instance)
        solver_name = "exact_small_scale"
    decisions = option_ids_to_decisions(instance, selection)
    return SolverResult(
        solver_name=solver_name,
        decisions=decisions,
        objective_value=objective,
        runtime_s=time.perf_counter() - start,
        violations=validate_decisions(instance, decisions),
        metadata={"backend": backend},
    )
