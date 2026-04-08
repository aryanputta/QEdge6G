from __future__ import annotations

import math
from collections import defaultdict

from src.utils.models import AllocationDecision, OptimizationInstance


def all_options(instance: OptimizationInstance) -> dict[str, object]:
    return {
        option.option_id: option
        for options in instance.options_by_user.values()
        for option in options
    }


def empty_usage(instance: OptimizationInstance) -> dict[str, int]:
    return {name: 0 for name in instance.capacities}


def is_feasible(instance: OptimizationInstance, option, usage: dict[str, int]) -> bool:
    if not option.admitted:
        return True
    for name, constraint in instance.capacities.items():
        weight = constraint.option_weights.get(option.option_id, 0)
        if usage[name] + weight > constraint.capacity_units:
            return False
    return True


def apply_option(instance: OptimizationInstance, option, usage: dict[str, int]) -> None:
    if not option.admitted:
        return
    for name, constraint in instance.capacities.items():
        usage[name] += constraint.option_weights.get(option.option_id, 0)


def option_ids_to_decisions(instance: OptimizationInstance, option_ids: list[str]) -> list[AllocationDecision]:
    lookup = all_options(instance)
    decisions: list[AllocationDecision] = []
    for user_id in instance.options_by_user:
        option = lookup[next(option_id for option_id in option_ids if lookup[option_id].user_id == user_id)]
        decisions.append(
            AllocationDecision(
                user_id=user_id,
                option_id=option.option_id,
                edge_id=None if not option.admitted else option.edge_id,
                path_id=None if not option.admitted else option.path_id,
                service_tier=option.service_tier,
                admitted=option.admitted,
                allocated_mbps=option.allocated_mbps,
                goodput_mbps=option.estimated_goodput_mbps if option.admitted else 0.0,
                packet_loss_rate=option.estimated_loss_rate if option.admitted else 1.0,
                latency_ms=option.estimated_latency_ms,
                queue_delay_ms=float(option.metadata.get("path_base_latency_ms", 0.0)) if option.admitted else 0.0,
                compute_delay_ms=float(option.metadata.get("edge_queue_delay_ms", 0.0)) if option.admitted else 0.0,
                objective_cost=option.objective_cost,
                metadata=dict(option.metadata),
            )
        )
    return decisions


def objective_from_option_ids(instance: OptimizationInstance, option_ids: list[str]) -> float:
    lookup = all_options(instance)
    return float(sum(lookup[option_id].objective_cost for option_id in option_ids))


def sorted_user_order(instance: OptimizationInstance) -> list[str]:
    users = list(instance.users.values())
    users.sort(key=lambda user: (-user.workload.priority, -user.demand_mbps))
    return [user.user_id for user in users]


def bottleneck_spread(instance: OptimizationInstance, option_ids: list[str]) -> dict[str, float]:
    usage = empty_usage(instance)
    lookup = all_options(instance)
    for option_id in option_ids:
        apply_option(instance, lookup[option_id], usage)
    summary = defaultdict(float)
    for name, constraint in instance.capacities.items():
        summary[name.split("::", maxsplit=1)[0]] = max(
            summary[name.split("::", maxsplit=1)[0]],
            usage[name] / max(1, constraint.capacity_units),
        )
    return dict(summary)


def min_remaining_bound(instance: OptimizationInstance, remaining_users: list[str]) -> float:
    return float(sum(min(option.objective_cost for option in instance.options_by_user[user_id]) for user_id in remaining_users))


def geometric_cooling(initial_temp: float, final_temp: float, steps: int, index: int) -> float:
    if steps <= 1:
        return final_temp
    ratio = math.exp(math.log(final_temp / initial_temp) / max(1, steps - 1))
    return initial_temp * (ratio ** index)

