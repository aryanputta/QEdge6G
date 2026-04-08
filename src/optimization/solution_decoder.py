from __future__ import annotations

from collections import defaultdict

import numpy as np

from src.optimization.constraints import find_violations
from src.optimization.qubo_builder import QUBOModel
from src.utils.models import AllocationDecision, OptimizationInstance


def _option_lookup(instance: OptimizationInstance) -> dict[str, object]:
    return {
        option.option_id: option
        for options in instance.options_by_user.values()
        for option in options
    }


def encode_selection_bits(instance: OptimizationInstance, qubo: QUBOModel, option_ids: list[str]) -> np.ndarray:
    bits = np.zeros(len(qubo.variables), dtype=int)
    for option_id in option_ids:
        index = qubo.option_to_index.get(option_id)
        if index is not None:
            bits[index] = 1
    for constraint in instance.capacities.values():
        consumed = sum(constraint.option_weights.get(option_id, 0) for option_id in option_ids)
        slack = max(0, constraint.capacity_units - consumed)
        for index, variable in enumerate(qubo.variables):
            if variable.kind != "slack" or variable.constraint_name != constraint.name:
                continue
            if slack >= variable.weight:
                bits[index] = 1
                slack -= variable.weight
    return bits


def decode_bits(instance: OptimizationInstance, qubo: QUBOModel, bits: np.ndarray) -> tuple[list[AllocationDecision], list[str]]:
    lookup = _option_lookup(instance)
    selected_options_by_user: dict[str, list[object]] = defaultdict(list)
    for index, bit in enumerate(bits):
        if not bit:
            continue
        variable = qubo.variables[index]
        if variable.kind == "option" and variable.option_id in lookup:
            option = lookup[variable.option_id]
            selected_options_by_user[option.user_id].append(option)

    decisions: list[AllocationDecision] = []
    chosen_option_ids: list[str] = []
    for user_id, options in instance.options_by_user.items():
        selected = selected_options_by_user.get(user_id, [])
        if not selected:
            chosen = next(option for option in options if option.option_id.endswith("::drop"))
        else:
            chosen = min(selected, key=lambda option: option.objective_cost)
        chosen_option_ids.append(chosen.option_id)
        decisions.append(
            AllocationDecision(
                user_id=user_id,
                option_id=chosen.option_id,
                edge_id=None if not chosen.admitted else chosen.edge_id,
                path_id=None if not chosen.admitted else chosen.path_id,
                service_tier=chosen.service_tier,
                admitted=chosen.admitted,
                allocated_mbps=chosen.allocated_mbps,
                goodput_mbps=chosen.estimated_goodput_mbps if chosen.admitted else 0.0,
                packet_loss_rate=chosen.estimated_loss_rate if chosen.admitted else 1.0,
                latency_ms=chosen.estimated_latency_ms,
                queue_delay_ms=float(chosen.metadata.get("path_base_latency_ms", 0.0)) if chosen.admitted else 0.0,
                compute_delay_ms=float(chosen.metadata.get("edge_queue_delay_ms", 0.0)) if chosen.admitted else 0.0,
                objective_cost=chosen.objective_cost,
                metadata=dict(chosen.metadata),
            )
        )
    violations = find_violations(instance, chosen_option_ids)
    return decisions, violations

