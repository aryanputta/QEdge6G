from __future__ import annotations

from src.utils.models import UserState


def demand_features(user: UserState) -> dict[str, float]:
    history = user.history_demand_mbps[-5:]
    return {
        "mean_recent_demand": sum(history) / max(1, len(history)),
        "latest_demand": history[-1] if history else user.demand_mbps,
        "channel_quality": user.channel_quality,
        "priority": user.workload.priority,
    }


def congestion_features(path_utilization: float, queue_delay_ms: float, loss_rate: float) -> dict[str, float]:
    return {
        "path_utilization": path_utilization,
        "queue_delay_ms": queue_delay_ms,
        "loss_rate": loss_rate,
    }

