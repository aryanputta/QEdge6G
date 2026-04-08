from __future__ import annotations

import math
import time

import numpy as np

from src.optimization.qubo_builder import build_qubo, qubo_energy
from src.optimization.solution_decoder import decode_bits, encode_selection_bits
from src.solvers.greedy_solver import solve as solve_greedy
from src.utils.models import OptimizationInstance, SolverResult


def _anneal(
    instance: OptimizationInstance,
    steps: int,
    seed: int,
    initial_temp: float,
    final_temp: float,
    initial_option_ids: list[str] | None = None,
) -> tuple[np.ndarray, float]:
    rng = np.random.default_rng(seed)
    qubo = build_qubo(instance)
    if initial_option_ids is None:
        greedy_result = solve_greedy(instance)
        current_option_ids = [decision.option_id for decision in greedy_result.decisions]
    else:
        current_option_ids = initial_option_ids
    current_bits = encode_selection_bits(instance, qubo, current_option_ids)
    current_energy = qubo_energy(qubo, current_bits)
    best_bits = current_bits.copy()
    best_energy = current_energy

    user_ids = list(instance.options_by_user)
    for step in range(steps):
        user_id = str(rng.choice(user_ids))
        candidate_option = rng.choice(instance.options_by_user[user_id])
        proposal_option_ids = [decision.option_id for decision in decode_bits(instance, qubo, current_bits)[0] if decision.user_id != user_id]
        proposal_option_ids.append(candidate_option.option_id)
        proposal_bits = encode_selection_bits(instance, qubo, proposal_option_ids)
        proposal_energy = qubo_energy(qubo, proposal_bits)

        temperature = initial_temp * math.exp(math.log(final_temp / initial_temp) * step / max(1, steps - 1))
        if proposal_energy < current_energy or rng.random() < math.exp((current_energy - proposal_energy) / max(temperature, 1e-6)):
            current_bits = proposal_bits
            current_energy = proposal_energy
        if current_energy < best_energy:
            best_bits = current_bits.copy()
            best_energy = current_energy
    return best_bits, best_energy


def solve(
    instance: OptimizationInstance,
    seed: int = 7,
    steps: int = 400,
    initial_option_ids: list[str] | None = None,
) -> SolverResult:
    start = time.perf_counter()
    qubo = build_qubo(instance)
    best_bits, best_energy = _anneal(
        instance,
        steps=steps,
        seed=seed,
        initial_temp=25.0,
        final_temp=0.3,
        initial_option_ids=initial_option_ids,
    )
    decisions, violations = decode_bits(instance, qubo, best_bits)
    objective = sum(decision.objective_cost for decision in decisions)
    return SolverResult(
        solver_name="simulated_annealing",
        decisions=decisions,
        objective_value=objective,
        runtime_s=time.perf_counter() - start,
        violations=violations,
        energy=best_energy,
        metadata={**qubo.metadata, "warm_start": initial_option_ids is not None},
    )
