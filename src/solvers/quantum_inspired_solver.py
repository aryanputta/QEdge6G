from __future__ import annotations

import math
import time

import numpy as np

from src.optimization.qubo_builder import build_qubo, qubo_energy
from src.optimization.solution_decoder import decode_bits, encode_selection_bits
from src.solvers.greedy_solver import solve as solve_greedy
from src.utils.models import OptimizationInstance, SolverResult


def _decision_p95(decisions) -> float:
    latencies = sorted(decision.latency_ms for decision in decisions if decision.admitted)
    if not latencies:
        return float("inf")
    return latencies[min(len(latencies) - 1, int(round(0.95 * (len(latencies) - 1))))]


def solve(
    instance: OptimizationInstance,
    seed: int = 11,
    steps: int = 420,
    initial_option_ids: list[str] | None = None,
) -> SolverResult:
    start = time.perf_counter()
    rng = np.random.default_rng(seed)
    qubo = build_qubo(instance)
    greedy_result = solve_greedy(instance)
    greedy_ids = initial_option_ids or [decision.option_id for decision in greedy_result.decisions]
    current_ids = greedy_ids.copy()
    current_bits = encode_selection_bits(instance, qubo, current_ids)
    current_energy = qubo_energy(qubo, current_bits)
    best_ids = current_ids.copy()
    best_energy = current_energy
    user_ids = list(instance.options_by_user)
    stagnation = 0

    for step in range(steps):
        move_size = 2 if rng.random() < 0.35 else 1
        chosen_users = rng.choice(user_ids, size=move_size, replace=False)
        proposal_ids = [option_id for option_id in current_ids if not any(option_id.startswith(f"{user_id}::") for user_id in chosen_users)]
        for user_id in chosen_users:
            options = instance.options_by_user[str(user_id)]
            if rng.random() < 0.25:
                shortlisted = options[: max(2, len(options) // 2)]
            else:
                shortlisted = options
            proposal_ids.append(str(rng.choice([option.option_id for option in shortlisted])))

        proposal_bits = encode_selection_bits(instance, qubo, proposal_ids)
        proposal_energy = qubo_energy(qubo, proposal_bits)

        if step and stagnation and stagnation % 60 == 0:
            temperature = 8.0
        else:
            temperature = 18.0 * math.exp(-3.8 * step / max(1, steps))

        accept = proposal_energy < current_energy or rng.random() < math.exp((current_energy - proposal_energy) / max(temperature, 1e-6))
        if accept:
            current_ids = proposal_ids
            current_bits = proposal_bits
            current_energy = proposal_energy
            stagnation = 0
        else:
            stagnation += 1

        if current_energy < best_energy:
            best_ids = current_ids.copy()
            best_energy = current_energy

    best_bits = encode_selection_bits(instance, qubo, best_ids)
    decisions, violations = decode_bits(instance, qubo, best_bits)
    optimized_goodput = sum(decision.goodput_mbps for decision in decisions)
    greedy_goodput = sum(decision.goodput_mbps for decision in greedy_result.decisions)
    optimized_p95 = _decision_p95(decisions)
    greedy_p95 = _decision_p95(greedy_result.decisions)
    if violations or (optimized_goodput < 0.82 * greedy_goodput and optimized_p95 > 1.05 * greedy_p95) or optimized_p95 > 1.12 * greedy_p95:
        decisions = greedy_result.decisions
        violations = greedy_result.violations
        best_energy = None
        selected_objective = greedy_result.objective_value
        safety_fallback = True
    else:
        selected_objective = sum(decision.objective_cost for decision in decisions)
        safety_fallback = False
    return SolverResult(
        solver_name="quantum_inspired",
        decisions=decisions,
        objective_value=selected_objective,
        runtime_s=time.perf_counter() - start,
        violations=violations,
        energy=best_energy,
        metadata={
            "move_set": "single+block",
            "reheating": True,
            "warm_start": initial_option_ids is not None,
            "safety_fallback": safety_fallback,
            **qubo.metadata,
        },
    )
