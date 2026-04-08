from __future__ import annotations

from collections import defaultdict

from src.utils.models import CapacityConstraint, OptimizationInstance


def option_lookup(instance: OptimizationInstance) -> dict[str, object]:
    lookup = {}
    for options in instance.options_by_user.values():
        for option in options:
            lookup[option.option_id] = option
    return lookup


def resource_usage(instance: OptimizationInstance, option_ids: list[str]) -> dict[str, int]:
    usage = defaultdict(int)
    for constraint in instance.capacities.values():
        for option_id in option_ids:
            usage[constraint.name] += constraint.option_weights.get(option_id, 0)
    return dict(usage)


def find_violations(instance: OptimizationInstance, option_ids: list[str]) -> list[str]:
    lookup = option_lookup(instance)
    violations: list[str] = []
    seen_users = defaultdict(int)
    for option_id in option_ids:
        option = lookup[option_id]
        seen_users[option.user_id] += 1
    for user_id, count in seen_users.items():
        if count != 1:
            violations.append(f"user::{user_id} expected 1 decision, found {count}")
    usage = resource_usage(instance, option_ids)
    for constraint in instance.capacities.values():
        if usage.get(constraint.name, 0) > constraint.capacity_units:
            violations.append(
                f"{constraint.name} exceeds {constraint.capacity_units} with {usage[constraint.name]}"
            )
    for user_id in instance.options_by_user:
        if seen_users.get(user_id, 0) == 0:
            violations.append(f"user::{user_id} has no selected option")
    return violations


def binding_resource(transport_util: float, wireless_util: float, edge_util: float, solver_runtime_s: float) -> str:
    bottlenecks = {
        "transport": transport_util,
        "wireless": wireless_util,
        "edge": edge_util,
        "solver": min(1.0, solver_runtime_s / 1.0),
    }
    return max(bottlenecks, key=bottlenecks.get)


def capacity_constraint(name: str, capacity_units: int, option_weights: dict[str, int]) -> CapacityConstraint:
    return CapacityConstraint(name=name, capacity_units=capacity_units, option_weights=option_weights)

