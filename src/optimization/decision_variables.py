from __future__ import annotations

import math

from src.edge.compute_queue import ComputeQueue
from src.optimization.constraints import capacity_constraint
from src.optimization.objective import drop_cost, option_cost
from src.utils.models import CandidateOption, OptimizationInstance, ServiceTier, UserState
from src.wireless.radio_model import estimate_radio_capacity_mbps, required_radio_units
from src.workloads.traffic_profiles import DEFAULT_SERVICE_TIERS


def _service_tiers() -> list[ServiceTier]:
    return [ServiceTier(name=name, throughput_factor=factor, utility_weight=utility) for name, factor, utility in DEFAULT_SERVICE_TIERS]


def build_optimization_instance(
    config: dict,
    scenario_name: str,
    time_slot: int,
    users: dict[str, UserState],
    topology,
    paths_by_pair: dict[tuple[str, str], list],
    edge_queues: dict[str, ComputeQueue],
) -> OptimizationInstance:
    solver_cfg = config["solver"]
    wireless_cfg = config["wireless"]
    slice_cfg = config["traffic"].get("slices", {})
    bandwidth_unit = int(solver_cfg.get("bandwidth_unit_mbps", 10))
    radio_unit_mhz = int(solver_cfg.get("radio_unit_mhz", 5))
    candidate_edges_per_user = int(solver_cfg.get("candidate_edges_per_user", 2))
    candidate_paths_per_edge = int(solver_cfg.get("candidate_paths_per_edge", 2))

    options_by_user: dict[str, list[CandidateOption]] = {}
    path_weights: dict[str, int] = {}
    edge_weights: dict[str, int] = {}
    radio_weights: dict[str, int] = {}
    fairness_floor = solver_cfg.get("fairness_reward_floor", 4.0)

    for user in users.values():
        station = topology.base_stations[user.attached_bs]
        radio_capacity = estimate_radio_capacity_mbps(
            user=user,
            station=station,
            active_users=len(users),
            num_base_stations=len(topology.base_stations),
            aggressiveness=float(wireless_cfg.get("interference_aggressiveness", 0.2)),
        )
        ranked_edges = []
        for edge_id in topology.edges:
            best_path = min(paths_by_pair[(user.attached_bs, edge_id)], key=lambda path: path.base_latency_ms + path.queue_delay_ms)
            ranked_edges.append((best_path.base_latency_ms + best_path.queue_delay_ms, edge_id))
        ranked_edges.sort(key=lambda item: item[0])
        selected_edges = [edge_id for _, edge_id in ranked_edges[:candidate_edges_per_user]]

        user_options: list[CandidateOption] = [
            CandidateOption(
                option_id=f"{user.user_id}::drop",
                user_id=user.user_id,
                bs_id=user.attached_bs,
                edge_id="drop",
                path_id="drop",
                service_tier="drop",
                admitted=False,
                allocated_mbps=0.0,
                compute_units=0,
                radio_units=0,
                path_units=0,
                estimated_latency_ms=user.workload.latency_sla_ms * 3.0,
                estimated_loss_rate=1.0,
                estimated_goodput_mbps=0.0,
                objective_cost=drop_cost(user),
            )
        ]

        fairness_bias = fairness_floor - min(fairness_floor, sum(user.history_demand_mbps[-3:]) / max(user.workload.base_demand_mbps, 1.0))
        slice_priority = float(slice_cfg.get(user.slice_id, {}).get("priority_weight", 1.0))
        for edge_id in selected_edges:
            server = topology.edges[edge_id]
            for path in paths_by_pair[(user.attached_bs, edge_id)][:candidate_paths_per_edge]:
                for tier in _service_tiers():
                    allocated = min(
                        user.predicted_demand_mbps * tier.throughput_factor,
                        radio_capacity,
                        path.capacity_mbps,
                    )
                    if allocated < max(1.0, 0.35 * user.workload.base_demand_mbps):
                        continue
                    radio_units = required_radio_units(allocated, user.spectral_efficiency, radio_unit_mhz)
                    path_units = max(1, math.ceil(allocated / bandwidth_unit))
                    compute_units = max(1, math.ceil(user.workload.compute_demand_units * tier.throughput_factor))
                    edge_queue_delay = edge_queues[edge_id].delay_ms
                    cost, latency_ms, goodput_mbps = option_cost(
                        user=user,
                        path=path,
                        server=server,
                        allocated_mbps=allocated,
                        radio_capacity_mbps=radio_capacity,
                        edge_queue_delay_ms=edge_queue_delay,
                        tier_utility=tier.utility_weight * slice_priority,
                        fairness_bias=fairness_bias,
                    )
                    option = CandidateOption(
                        option_id=f"{user.user_id}::{edge_id}::{path.path_id}::{tier.name}",
                        user_id=user.user_id,
                        bs_id=user.attached_bs,
                        edge_id=edge_id,
                        path_id=path.path_id,
                        service_tier=tier.name,
                        admitted=True,
                        allocated_mbps=allocated,
                        compute_units=compute_units,
                        radio_units=radio_units,
                        path_units=path_units,
                        estimated_latency_ms=latency_ms,
                        estimated_loss_rate=path.loss_rate,
                        estimated_goodput_mbps=goodput_mbps,
                        objective_cost=cost,
                        metadata={
                            "path_utilization": path.utilization,
                            "path_base_latency_ms": path.base_latency_ms,
                            "edge_queue_delay_ms": edge_queue_delay,
                            "radio_capacity_mbps": radio_capacity,
                            "tenant_id": user.tenant_id,
                            "slice_id": user.slice_id,
                        },
                    )
                    if radio_units <= station.spectrum_mhz // radio_unit_mhz and path_units <= max(1, path.capacity_mbps // bandwidth_unit):
                        user_options.append(option)
                        path_weights[option.option_id] = option.path_units
                        edge_weights[option.option_id] = option.compute_units
                        radio_weights[option.option_id] = option.radio_units
        options_by_user[user.user_id] = sorted(user_options, key=lambda option: option.objective_cost)

    capacities = {}
    for bs_id, station in topology.base_stations.items():
        name = f"radio::{bs_id}"
        capacities[name] = capacity_constraint(
            name=name,
            capacity_units=max(1, station.spectrum_mhz // radio_unit_mhz),
            option_weights={option.option_id: option.radio_units for options in options_by_user.values() for option in options if option.bs_id == bs_id},
        )
        for slice_id, params in slice_cfg.items():
            max_share = float(params.get("max_radio_share", 1.0))
            capacities[f"slice_radio::{bs_id}::{slice_id}"] = capacity_constraint(
                name=f"slice_radio::{bs_id}::{slice_id}",
                capacity_units=max(1, int((station.spectrum_mhz // radio_unit_mhz) * max_share)),
                option_weights={
                    option.option_id: option.radio_units
                    for options in options_by_user.values()
                    for option in options
                    if option.bs_id == bs_id and instance_slice(option, users) == slice_id
                },
            )
    for edge_id, server in topology.edges.items():
        name = f"edge::{edge_id}"
        capacities[name] = capacity_constraint(
            name=name,
            capacity_units=server.capacity_units,
            option_weights={option.option_id: option.compute_units for options in options_by_user.values() for option in options if option.edge_id == edge_id},
        )
        for slice_id, params in slice_cfg.items():
            max_share = float(params.get("max_edge_share", 1.0))
            capacities[f"slice_edge::{edge_id}::{slice_id}"] = capacity_constraint(
                name=f"slice_edge::{edge_id}::{slice_id}",
                capacity_units=max(1, int(server.capacity_units * max_share)),
                option_weights={
                    option.option_id: option.compute_units
                    for options in options_by_user.values()
                    for option in options
                    if option.edge_id == edge_id and instance_slice(option, users) == slice_id
                },
            )
    for candidate_paths in paths_by_pair.values():
        for path in candidate_paths:
            name = f"path::{path.path_id}"
            capacities[name] = capacity_constraint(
                name=name,
                capacity_units=max(1, path.capacity_mbps // bandwidth_unit),
                option_weights={option.option_id: option.path_units for options in options_by_user.values() for option in options if option.path_id == path.path_id},
            )

    return OptimizationInstance(
        scenario_name=scenario_name,
        time_slot=time_slot,
        users=users,
        options_by_user=options_by_user,
        capacities=capacities,
        metadata={
            "bandwidth_unit_mbps": bandwidth_unit,
            "radio_unit_mhz": radio_unit_mhz,
            "qubo_penalty_scale": float(solver_cfg.get("qubo_penalty_scale", 44.0)),
            "qubo_capacity_penalty_scale": float(solver_cfg.get("qubo_capacity_penalty_scale", 24.0)),
            "milp_time_limit_s": float(solver_cfg.get("milp_time_limit_s", 20.0)),
        },
    )


def instance_slice(option, users: dict[str, UserState]) -> str:
    return users[option.user_id].slice_id
