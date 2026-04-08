from __future__ import annotations

from collections import Counter


def dominant_bottleneck(rows: list[dict]) -> str:
    counts = Counter(row["dominant_bottleneck"] for row in rows)
    return counts.most_common(1)[0][0] if counts else "unknown"

