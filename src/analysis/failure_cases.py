from __future__ import annotations


def worst_tail_latency(rows: list[dict]) -> dict:
    if not rows:
        return {}
    return max(rows, key=lambda row: float(row["p99_latency_ms"]))

