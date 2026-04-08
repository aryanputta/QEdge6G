from __future__ import annotations


def summarize_sensitivity(metric_rows: list[dict], field: str) -> dict[str, float]:
    values = [float(row[field]) for row in metric_rows]
    return {
        "min": min(values) if values else 0.0,
        "max": max(values) if values else 0.0,
        "mean": sum(values) / len(values) if values else 0.0,
    }

