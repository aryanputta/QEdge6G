from __future__ import annotations

from src.optimization.ising_converter import qubo_to_ising
from src.optimization.qubo_builder import build_qubo
from src.utils.models import OptimizationInstance


def export_hamiltonian(instance: OptimizationInstance) -> dict[str, object]:
    qubo = build_qubo(instance)
    h, j, offset = qubo_to_ising(qubo)
    return {
        "h": h.tolist(),
        "J": j.tolist(),
        "offset": offset,
        "metadata": {
            "note": "QAOA export only. No quantum backend is bundled in this repository.",
            **qubo.metadata,
        },
    }


def solve(instance: OptimizationInstance):  # pragma: no cover - intentionally export-only
    raise RuntimeError("QAOA solve is export-only in this repo. Use export_hamiltonian() with a backend of your choice.")

