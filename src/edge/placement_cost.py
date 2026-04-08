from __future__ import annotations

from src.utils.models import EdgeServer, WorkloadClass


def placement_cost(workload: WorkloadClass, server: EdgeServer, transport_latency_ms: float) -> float:
    compute_pressure = workload.compute_demand_units / max(server.capacity_units, 1)
    return transport_latency_ms * 0.4 + compute_pressure * 12.0 + server.energy_cost

