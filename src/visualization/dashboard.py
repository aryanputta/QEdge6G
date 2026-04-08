from __future__ import annotations


def summarize_dashboard(rows: list[dict]) -> dict[str, float]:
    if not rows:
        return {}
    return {
        "best_p95_latency_ms": min(float(row["p95_latency_ms"]) for row in rows),
        "best_fairness_index": max(float(row["fairness_index"]) for row in rows),
        "lowest_runtime_s": min(float(row["solver_runtime_s"]) for row in rows),
    }

