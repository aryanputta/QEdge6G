from __future__ import annotations

from src.utils.models import WorkloadClass


def default_workload_classes() -> dict[str, WorkloadClass]:
    return {
        "xr": WorkloadClass("xr", latency_sla_ms=18.0, base_demand_mbps=30.0, compute_demand_units=6, priority=1.5, burstiness=0.25),
        "video": WorkloadClass("video", latency_sla_ms=45.0, base_demand_mbps=16.0, compute_demand_units=4, priority=1.0, burstiness=0.35),
        "inference": WorkloadClass("inference", latency_sla_ms=28.0, base_demand_mbps=12.0, compute_demand_units=7, priority=1.3, burstiness=0.20),
        "telemetry": WorkloadClass("telemetry", latency_sla_ms=80.0, base_demand_mbps=4.0, compute_demand_units=2, priority=0.7, burstiness=0.10),
    }

