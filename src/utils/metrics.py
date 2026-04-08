from __future__ import annotations

from typing import Iterable

import numpy as np

from src.utils.models import AllocationDecision, StepMetrics


def jain_fairness(values: Iterable[float]) -> float:
    array = np.asarray(list(values), dtype=float)
    if array.size == 0:
        return 1.0
    if np.allclose(array.sum(), 0.0):
        return 0.0
    return float((array.sum() ** 2) / (array.size * np.square(array).sum()))


def percentile(values: Iterable[float], pct: float) -> float:
    array = np.asarray(list(values), dtype=float)
    if array.size == 0:
        return 0.0
    return float(np.percentile(array, pct))


def summarize_step(
    scenario_name: str,
    time_slot: int,
    solver_name: str,
    decisions: list[AllocationDecision],
    objective_value: float,
    runtime_s: float,
    quality_gap: float | None,
    violation_count: int,
    transport_utilization: float,
    wireless_utilization: float,
    edge_utilization: float,
    dominant_bottleneck: str,
) -> StepMetrics:
    latencies = [decision.latency_ms for decision in decisions if decision.admitted]
    throughputs = [decision.allocated_mbps for decision in decisions if decision.admitted]
    goodputs = [decision.goodput_mbps for decision in decisions if decision.admitted]
    losses = [decision.packet_loss_rate for decision in decisions if decision.admitted]
    queue_delays = [decision.queue_delay_ms + decision.compute_delay_ms for decision in decisions if decision.admitted]
    admission_rate = sum(1 for decision in decisions if decision.admitted) / max(len(decisions), 1)
    return StepMetrics(
        scenario_name=scenario_name,
        time_slot=time_slot,
        solver_name=solver_name,
        mean_latency_ms=float(np.mean(latencies)) if latencies else 0.0,
        p95_latency_ms=percentile(latencies, 95),
        p99_latency_ms=percentile(latencies, 99),
        throughput_mbps=float(np.sum(throughputs)),
        goodput_mbps=float(np.sum(goodputs)),
        packet_loss_rate=float(np.mean(losses)) if losses else 0.0,
        fairness_index=jain_fairness(goodputs if goodputs else [0.0]),
        queue_delay_ms=float(np.mean(queue_delays)) if queue_delays else 0.0,
        edge_utilization=edge_utilization,
        transport_utilization=transport_utilization,
        wireless_utilization=wireless_utilization,
        solver_runtime_s=runtime_s,
        objective_value=objective_value,
        quality_gap=quality_gap,
        constraint_violation_count=violation_count,
        dominant_bottleneck=dominant_bottleneck,
        admission_rate=admission_rate,
    )


def aggregate_metrics(rows: list[StepMetrics]) -> dict[str, float | str | None]:
    if not rows:
        return {}
    numeric_keys = [
        "mean_latency_ms",
        "p95_latency_ms",
        "p99_latency_ms",
        "throughput_mbps",
        "goodput_mbps",
        "packet_loss_rate",
        "fairness_index",
        "queue_delay_ms",
        "edge_utilization",
        "transport_utilization",
        "wireless_utilization",
        "solver_runtime_s",
        "objective_value",
        "constraint_violation_count",
        "admission_rate",
    ]
    aggregated: dict[str, float | str | None] = {}
    for key in numeric_keys:
        aggregated[key] = float(np.mean([getattr(row, key) for row in rows]))
    quality_gaps = [row.quality_gap for row in rows if row.quality_gap is not None]
    aggregated["quality_gap"] = float(np.mean(quality_gaps)) if quality_gaps else None
    bottlenecks = {}
    for row in rows:
        bottlenecks[row.dominant_bottleneck] = bottlenecks.get(row.dominant_bottleneck, 0) + 1
    aggregated["dominant_bottleneck"] = max(bottlenecks, key=bottlenecks.get)
    return aggregated

