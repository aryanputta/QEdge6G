from __future__ import annotations

import math
import time

import numpy as np

from src.optimization.qubo_builder import build_qubo, qubo_energy
from src.optimization.solution_decoder import decode_bits, encode_selection_bits
from src.solvers.greedy_solver import solve as solve_greedy
from src.utils.models import OptimizationInstance, SolverResult


def solve(
    instance: OptimizationInstance,
    seed: int = 7,
    sweeps: int = 120,
    replicas: int = 4,
    initial_option_ids: list[str] | None = None,
) -> SolverResult:
    start = time.perf_counter()
    rng = np.random.default_rng(seed)
    qubo = build_qubo(instance)
    greedy_ids = initial_option_ids or [decision.option_id for decision in solve_greedy(instance).decisions]
    user_ids = list(instance.options_by_user)
    temperatures = np.linspace(0.5, 20.0, replicas)
    states = [encode_selection_bits(instance, qubo, greedy_ids) for _ in range(replicas)]
    energies = [qubo_energy(qubo, state) for state in states]
    best_state = states[int(np.argmin(energies))].copy()
    best_energy = min(energies)

    for _ in range(sweeps):
        for replica in range(replicas):
            current = decode_bits(instance, qubo, states[replica])[0]
            current_ids = [decision.option_id for decision in current]
            user_id = str(rng.choice(user_ids))
            proposal_ids = [option_id for option_id in current_ids if not option_id.startswith(f"{user_id}::")]
            proposal_ids.append(str(rng.choice([option.option_id for option in instance.options_by_user[user_id]])))
            proposal = encode_selection_bits(instance, qubo, proposal_ids)
            proposal_energy = qubo_energy(qubo, proposal)
            delta = proposal_energy - energies[replica]
            temp = temperatures[replica]
            if delta < 0 or rng.random() < math.exp(-delta / max(temp, 1e-6)):
                states[replica] = proposal
                energies[replica] = proposal_energy
        for replica in range(replicas - 1):
            delta = (1.0 / temperatures[replica] - 1.0 / temperatures[replica + 1]) * (energies[replica + 1] - energies[replica])
            if delta >= 0 or rng.random() < math.exp(delta):
                states[replica], states[replica + 1] = states[replica + 1], states[replica]
                energies[replica], energies[replica + 1] = energies[replica + 1], energies[replica]
        replica_best = int(np.argmin(energies))
        if energies[replica_best] < best_energy:
            best_energy = energies[replica_best]
            best_state = states[replica_best].copy()

    decisions, violations = decode_bits(instance, qubo, best_state)
    return SolverResult(
        solver_name="parallel_tempering",
        decisions=decisions,
        objective_value=sum(decision.objective_cost for decision in decisions),
        runtime_s=time.perf_counter() - start,
        violations=violations,
        energy=best_energy,
        metadata={"replicas": replicas, "warm_start": initial_option_ids is not None, **qubo.metadata},
    )
