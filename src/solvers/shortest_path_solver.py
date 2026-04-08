from __future__ import annotations

import time

from src.optimization.validator import validate_decisions
from src.solvers.common import apply_option, empty_usage, is_feasible, objective_from_option_ids, option_ids_to_decisions, sorted_user_order
from src.utils.models import OptimizationInstance, SolverResult


def solve(instance: OptimizationInstance, initial_option_ids: list[str] | None = None) -> SolverResult:
    del initial_option_ids
    start = time.perf_counter()
    usage = empty_usage(instance)
    chosen_option_ids: list[str] = []
    for user_id in sorted_user_order(instance):
        options = sorted(
            instance.options_by_user[user_id],
            key=lambda option: (
                not option.admitted,
                option.metadata.get("path_base_latency_ms", float("inf")),
                option.metadata.get("edge_queue_delay_ms", float("inf")),
            ),
        )
        selected = next((option for option in options if is_feasible(instance, option, usage)), None)
        if selected is None:
            selected = next(option for option in options if not option.admitted)
        apply_option(instance, selected, usage)
        chosen_option_ids.append(selected.option_id)

    decisions = option_ids_to_decisions(instance, chosen_option_ids)
    return SolverResult(
        solver_name="shortest_path_nearest_edge",
        decisions=decisions,
        objective_value=objective_from_option_ids(instance, chosen_option_ids),
        runtime_s=time.perf_counter() - start,
        violations=validate_decisions(instance, decisions),
    )
