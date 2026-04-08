from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from src.utils.models import OptimizationInstance


@dataclass
class QUBOVariable:
    name: str
    kind: str
    option_id: str | None = None
    constraint_name: str | None = None
    weight: int = 0


@dataclass
class QUBOModel:
    matrix: np.ndarray
    variables: list[QUBOVariable]
    constant: float
    option_to_index: dict[str, int]
    metadata: dict


def _exact_binary_weights(capacity: int) -> list[int]:
    if capacity <= 0:
        return []
    weights = []
    remaining = capacity
    bit = 1
    while remaining > 0:
        weight = min(bit, remaining)
        weights.append(weight)
        remaining -= weight
        bit *= 2
    return weights


def _add_penalty(matrix: np.ndarray, coeffs: dict[int, int], target: int, penalty: float) -> float:
    constant = penalty * (target ** 2)
    indices = list(coeffs)
    for index in indices:
        coefficient = coeffs[index]
        matrix[index, index] += penalty * (coefficient ** 2 - 2 * target * coefficient)
    for left_pos, left in enumerate(indices):
        for right in indices[left_pos + 1 :]:
            matrix[left, right] += penalty * coeffs[left] * coeffs[right]
            matrix[right, left] = matrix[left, right]
    return constant


def build_qubo(
    instance: OptimizationInstance,
    penalty_scale: float | None = None,
    capacity_penalty_scale: float | None = None,
) -> QUBOModel:
    penalty_scale = float(instance.metadata.get("qubo_penalty_scale", 40.0)) if penalty_scale is None else penalty_scale
    capacity_penalty_scale = (
        float(instance.metadata.get("qubo_capacity_penalty_scale", 22.0))
        if capacity_penalty_scale is None
        else capacity_penalty_scale
    )
    variables: list[QUBOVariable] = []
    option_to_index: dict[str, int] = {}
    for options in instance.options_by_user.values():
        for option in options:
            option_to_index[option.option_id] = len(variables)
            variables.append(QUBOVariable(name=option.option_id, kind="option", option_id=option.option_id))

    constraint_slack_indices: dict[str, list[int]] = {}
    for constraint in instance.capacities.values():
        slack_indices = []
        for weight in _exact_binary_weights(constraint.capacity_units):
            slack_name = f"{constraint.name}::slack::{weight}::{len(slack_indices)}"
            slack_indices.append(len(variables))
            variables.append(QUBOVariable(name=slack_name, kind="slack", constraint_name=constraint.name, weight=weight))
        constraint_slack_indices[constraint.name] = slack_indices

    matrix = np.zeros((len(variables), len(variables)), dtype=float)
    constant = 0.0
    for options in instance.options_by_user.values():
        for option in options:
            matrix[option_to_index[option.option_id], option_to_index[option.option_id]] += option.objective_cost

    for user_id, options in instance.options_by_user.items():
        coeffs = {option_to_index[option.option_id]: 1 for option in options}
        constant += _add_penalty(matrix, coeffs, target=1, penalty=penalty_scale)

    for constraint in instance.capacities.values():
        coeffs = {
            option_to_index[option_id]: weight
            for option_id, weight in constraint.option_weights.items()
            if option_id in option_to_index
        }
        for slack_index in constraint_slack_indices[constraint.name]:
            coeffs[slack_index] = variables[slack_index].weight
        constant += _add_penalty(matrix, coeffs, target=constraint.capacity_units, penalty=capacity_penalty_scale)

    return QUBOModel(
        matrix=matrix,
        variables=variables,
        constant=constant,
        option_to_index=option_to_index,
        metadata={
            "num_variables": len(variables),
            "num_option_variables": len(option_to_index),
            "num_slack_variables": len(variables) - len(option_to_index),
        },
    )


def qubo_energy(qubo: QUBOModel, bits: np.ndarray) -> float:
    return float(bits @ qubo.matrix @ bits + qubo.constant)
