from __future__ import annotations


def scheduler_pressure(utilization: float, backlog_units: float) -> float:
    return min(2.0, utilization + backlog_units / 100.0)

