from __future__ import annotations


def summarize_fairness(rows: list[dict]) -> dict[str, float]:
    fairness = [float(row["fairness_index"]) for row in rows]
    return {
        "mean": sum(fairness) / len(fairness) if fairness else 0.0,
        "worst": min(fairness) if fairness else 0.0,
    }

