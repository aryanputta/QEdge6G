from __future__ import annotations

from collections import Counter

import numpy as np

from src.utils.models import UserState, WorkloadClass
from src.workloads.arrival_process import bursty_arrival
from src.workloads.trace_replay import TraceReplayDataset
from src.workloads.workload_classes import default_workload_classes


def sample_workload_name(workload_mix: dict[str, float], rng: np.random.Generator) -> str:
    names = list(workload_mix)
    probs = np.asarray([workload_mix[name] for name in names], dtype=float)
    probs = probs / probs.sum()
    return str(rng.choice(names, p=probs))


def _sample_tenant_and_slice(traffic_cfg: dict, rng: np.random.Generator) -> tuple[str, str]:
    tenants = traffic_cfg.get("tenants", {"tenant0": 0.5, "tenant1": 0.3, "tenant2": 0.2})
    tenant_names = list(tenants)
    tenant_probs = np.asarray([tenants[name] for name in tenant_names], dtype=float)
    tenant_probs = tenant_probs / tenant_probs.sum()
    tenant_id = str(rng.choice(tenant_names, p=tenant_probs))

    slices = traffic_cfg.get(
        "slices",
        {
            "URLLC": {"share": 0.2},
            "eMBB": {"share": 0.55},
            "mMTC": {"share": 0.25},
        },
    )
    slice_names = list(slices)
    slice_probs = np.asarray([slices[name].get("share", 1.0) for name in slice_names], dtype=float)
    slice_probs = slice_probs / slice_probs.sum()
    return tenant_id, str(rng.choice(slice_names, p=slice_probs))


def create_users(
    config: dict,
    rng: np.random.Generator,
    base_station_ids: list[str],
    trace_replay: TraceReplayDataset | None = None,
) -> dict[str, UserState]:
    traffic_cfg = config["traffic"]
    topology_cfg = config["topology"]
    classes = default_workload_classes()
    users: dict[str, UserState] = {}
    area_km = topology_cfg.get("area_km", 2.0)
    mobility = traffic_cfg.get("mobility_speed_mps", 1.0)
    mix = traffic_cfg.get("workload_mix", {"xr": 0.25, "video": 0.35, "inference": 0.25, "telemetry": 0.15})
    if trace_replay is not None:
        for record in trace_replay.initial_records():
            workload = classes.get(record.workload, classes["video"])
            users[record.user_id] = UserState(
                user_id=record.user_id,
                attached_bs=record.attached_bs,
                x=float(rng.uniform(0.0, area_km)),
                y=float(rng.uniform(0.0, area_km)),
                tenant_id=record.tenant_id,
                slice_id=record.slice_id,
                workload=workload,
                demand_mbps=record.demand_mbps,
                predicted_demand_mbps=record.demand_mbps,
                channel_quality=record.channel_quality,
                spectral_efficiency=2.5,
                mobility_speed=record.mobility_speed_mps,
                history_demand_mbps=[record.demand_mbps],
                history_channel_quality=[record.channel_quality],
            )
        return users

    for index in range(traffic_cfg["num_users"]):
        user_id = f"user{index}"
        workload_name = sample_workload_name(mix, rng)
        workload = classes[workload_name]
        attached_bs = base_station_ids[index % len(base_station_ids)]
        tenant_id, slice_id = _sample_tenant_and_slice(traffic_cfg, rng)
        users[user_id] = UserState(
            user_id=user_id,
            attached_bs=attached_bs,
            x=float(rng.uniform(0.0, area_km)),
            y=float(rng.uniform(0.0, area_km)),
            tenant_id=tenant_id,
            slice_id=slice_id,
            workload=workload,
            demand_mbps=workload.base_demand_mbps,
            predicted_demand_mbps=workload.base_demand_mbps,
            channel_quality=float(rng.uniform(0.45, 0.95)),
            spectral_efficiency=2.5,
            mobility_speed=float(mobility * rng.uniform(0.5, 1.2)),
        )
    return users


def update_user_demands(
    users: dict[str, UserState],
    rng: np.random.Generator,
    time_slot: int,
    trace_replay: TraceReplayDataset | None = None,
) -> Counter:
    demand_snapshot: Counter = Counter()
    if trace_replay is not None:
        records = trace_replay.slot_records(time_slot)
        for user in users.values():
            record = records.get(user.user_id)
            if record is not None:
                user.demand_mbps = record.demand_mbps
                user.channel_quality = record.channel_quality
                user.attached_bs = record.attached_bs
                user.mobility_speed = record.mobility_speed_mps
                user.tenant_id = record.tenant_id
                user.slice_id = record.slice_id
            user.history_demand_mbps.append(user.demand_mbps)
            user.history_channel_quality.append(user.channel_quality)
            demand_snapshot[user.user_id] = user.demand_mbps
        return demand_snapshot
    for user in users.values():
        user.demand_mbps = bursty_arrival(user.workload.base_demand_mbps, user.workload.burstiness, rng)
        user.history_demand_mbps.append(user.demand_mbps)
        demand_snapshot[user.user_id] = user.demand_mbps
    return demand_snapshot
