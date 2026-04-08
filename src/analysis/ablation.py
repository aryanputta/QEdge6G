from __future__ import annotations


def compare_metric(rows_with_ai: list[dict], rows_without_ai: list[dict], metric: str) -> dict[str, float]:
    mean_with = sum(float(row[metric]) for row in rows_with_ai) / max(1, len(rows_with_ai))
    mean_without = sum(float(row[metric]) for row in rows_without_ai) / max(1, len(rows_without_ai))
    return {
        "with_ai": mean_with,
        "without_ai": mean_without,
        "delta": mean_with - mean_without,
    }

