from __future__ import annotations

from collections import defaultdict

from src.edge.edge_server import compute_service_time_ms
from src.ml.inference_pipeline import InferencePipeline
from src.network.mobility import update_user_position
from src.network.path_finder import enumerate_paths
from src.optimization.constraints import binding_resource
from src.transport.quic_model import QUICFlowState, step_quic_flow
from src.transport.tcp_model import TCPFlowState, step_tcp_flow
from src.utils.metrics import summarize_step
from src.utils.models import AllocationDecision, OptimizationInstance, StepMetrics
from src.wireless.channel_state import evolve_channel_quality
from src.wireless.handoff import maybe_handoff
from src.wireless.spectral_efficiency import spectral_efficiency_from_quality
from src.workloads.traffic_generator import update_user_demands


def pre_step_update(
    config: dict,
    topology,
    users: dict,
    tracker,
    rng,
    time_slot: int,
    trace_replay=None,
) -> dict[tuple[str, str], list]:
    scenario_cfg = config["scenario"]
    area_km = config["topology"].get("area_km", 2.0)
    degradation_cfg = scenario_cfg.get("degradation_event", {})
    for link in topology.links.values():
        link.degraded_factor = 1.0
    if degradation_cfg and degradation_cfg.get("start_step", 10) <= time_slot < degradation_cfg.get("end_step", 10**9):
        for link_id in degradation_cfg.get("links", []):
            if link_id in topology.links:
                topology.links[link_id].degraded_factor = float(degradation_cfg.get("factor", 0.6))

    update_user_demands(users, rng, time_slot=time_slot, trace_replay=trace_replay)
    for user in users.values():
        if trace_replay is None:
            update_user_position(user, rng, area_km=area_km)
            maybe_handoff(
                user,
                topology.base_stations,
                time_slot=time_slot,
                hysteresis_km=float(config["wireless"].get("handoff_hysteresis_km", 0.05)),
                dwell_slots=int(config["wireless"].get("handoff_dwell_slots", 2)),
                blackout_penalty_ms=float(config["wireless"].get("handoff_blackout_penalty_ms", 4.0)),
            )
            user.channel_quality = evolve_channel_quality(
                current_quality=user.channel_quality,
                rng=rng,
                volatility=float(config["wireless"].get("channel_volatility", 0.08)),
                degradation=float(config["wireless"].get("degradation_bias", 0.0)),
            )
            user.history_channel_quality.append(user.channel_quality)
        user.spectral_efficiency = spectral_efficiency_from_quality(user.channel_quality)

    inference = InferencePipeline(enable_ai=bool(config["ml"].get("enabled", False)))
    inference.update_predictions(
        users,
        horizon=int(config["solver"].get("rolling_horizon_steps", 1)),
        forecast_error_std=float(config["ml"].get("forecast_error_std", 0.0)),
    )
    return enumerate_paths(topology, tracker.link_queues, k_paths=int(config["solver"].get("candidate_paths_per_edge", 2)) + 1)


def _path_lookup(paths_by_pair: dict[tuple[str, str], list]) -> dict[str, object]:
    return {
        path.path_id: path
        for paths in paths_by_pair.values()
        for path in paths
    }


def apply_decisions(
    config: dict,
    topology,
    tracker,
    instance: OptimizationInstance,
    decisions: list[AllocationDecision],
    paths_by_pair: dict[tuple[str, str], list],
    solver_name: str,
    objective_value: float,
    solver_runtime_s: float,
    quality_gap: float | None,
    violations: list[str],
) -> StepMetrics:
    path_lookup = _path_lookup(paths_by_pair)
    option_lookup = {
        option.option_id: option
        for options in instance.options_by_user.values()
        for option in options
    }
    link_loads = defaultdict(float)
    edge_arrivals = defaultdict(float)
    radio_loads = defaultdict(float)

    for decision in decisions:
        if not decision.admitted:
            continue
        option = option_lookup[decision.option_id]
        path = path_lookup[decision.path_id]
        for link_id in path.links:
            link_loads[link_id] += option.allocated_mbps
        edge_arrivals[decision.edge_id] += option.compute_units
        radio_loads[option.bs_id] += option.radio_units

    for link_id, queue in tracker.link_queues.items():
        queue.step(link_loads[link_id])
    for edge_id, queue in tracker.edge_queues.items():
        queue.step(edge_arrivals[edge_id])

    transport_mode = config["transport"].get("mode", "tcp")
    for decision in decisions:
        if not decision.admitted:
            continue
        option = option_lookup[decision.option_id]
        path = path_lookup[decision.path_id]
        path_queue_delay = sum(tracker.link_queues[link_id].delay_ms for link_id in path.links)
        path_loss = max(
            topology.links[link_id].loss_rate + tracker.link_queues[link_id].loss_rate
            for link_id in path.links
        )
        path_capacity = min(topology.links[link_id].capacity_mbps * topology.links[link_id].degraded_factor for link_id in path.links)
        rtt_ms = path.base_latency_ms + path_queue_delay

        if transport_mode == "quic":
            flow = tracker.quic_flows.setdefault(decision.user_id, QUICFlowState())
            send_rate, goodput, retransmission = step_quic_flow(flow, option.allocated_mbps, path_capacity, rtt_ms, path_loss)
        else:
            flow = tracker.tcp_flows.setdefault(decision.user_id, TCPFlowState())
            result = step_tcp_flow(flow, option.allocated_mbps, path_capacity, rtt_ms, path_loss)
            send_rate, goodput, retransmission = result.send_rate_mbps, result.goodput_mbps, result.retransmission_penalty_ms

        edge_server = topology.edges[decision.edge_id]
        compute_delay = tracker.edge_queues[decision.edge_id].delay_ms + compute_service_time_ms(edge_server, option.compute_units)
        station = topology.base_stations[option.bs_id]
        radio_capacity = max(1.0, option.metadata.get("radio_capacity_mbps", station.spectrum_mhz))
        radio_delay = 25.0 * send_rate / radio_capacity
        handoff_penalty_ms = instance.users[decision.user_id].handoff_penalty_ms
        decision.goodput_mbps = goodput
        decision.packet_loss_rate = min(1.0, path_loss)
        decision.queue_delay_ms = path_queue_delay
        decision.compute_delay_ms = compute_delay
        decision.latency_ms = radio_delay + rtt_ms + compute_delay + retransmission + handoff_penalty_ms
        decision.metadata["handoff_penalty_ms"] = handoff_penalty_ms

    max_transport_util = max((queue.utilization for queue in tracker.link_queues.values()), default=0.0)
    max_edge_util = max((queue.utilization for queue in tracker.edge_queues.values()), default=0.0)
    max_wireless_util = max(
        (
            radio_loads[bs_id] / max(1, constraint.capacity_units)
            for bs_id, constraint in (
                (name.split("::", maxsplit=1)[1], constraint)
                for name, constraint in instance.capacities.items()
                if name.startswith("radio::")
            )
        ),
        default=0.0,
    )
    dominant = binding_resource(
        transport_util=max_transport_util,
        wireless_util=max_wireless_util,
        edge_util=max_edge_util,
        solver_runtime_s=solver_runtime_s,
    )
    metrics = summarize_step(
        scenario_name=instance.scenario_name,
        time_slot=instance.time_slot,
        solver_name=solver_name,
        decisions=decisions,
        objective_value=objective_value,
        runtime_s=solver_runtime_s,
        quality_gap=quality_gap,
        violation_count=len(violations),
        transport_utilization=max_transport_util,
        wireless_utilization=max_wireless_util,
        edge_utilization=max_edge_util,
        dominant_bottleneck=dominant,
    )
    tracker.history.append(
        {
            "time_slot": instance.time_slot,
            "solver_name": solver_name,
            "metrics": metrics,
            "violations": list(violations),
        }
    )
    return metrics
