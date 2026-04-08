from __future__ import annotations

from src.optimization.qubo_builder import build_qubo
from src.optimization.solution_decoder import decode_bits, encode_selection_bits
from src.solvers.ilp_solver import solve as solve_exact


def test_decoder_round_trip_matches_exact_selection(optimization_instance):
    _, _, _, _, _, instance = optimization_instance
    result = solve_exact(instance)
    qubo = build_qubo(instance)
    option_ids = [decision.option_id for decision in result.decisions]
    bits = encode_selection_bits(instance, qubo, option_ids)
    decisions, violations = decode_bits(instance, qubo, bits)
    assert len(decisions) == len(instance.users)
    assert violations == []

