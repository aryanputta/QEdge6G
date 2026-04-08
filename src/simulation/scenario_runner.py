from __future__ import annotations

from dataclasses import asdict

from src.network.topology import build_topology
from src.optimization.decision_variables import build_optimization_instance
from src.simulation.event_loop import apply_decisions, pre_step_update
from src.simulation.state_tracker import initialize_state
from src.solvers import greedy_solver, ilp_solver, load_balanced_solver, parallel_tempering_solver, quantum_inspired_solver, shortest_path_solver, simulated_annealing_solver
from src.utils.metrics import aggregate_metrics
from src.utils.seed import seed_everything
from src.workloads.traffic_generator import create_users
from src.workloads.trace_replay import TraceReplayDataset


SOLVER_REGISTRY = {
    "greedy": greedy_solver.solve,
    "shortest_path": shortest_path_solver.solve,
    "load_balanced": load_balanced_solver.solve,
    "exact": ilp_solver.solve,
    "simulated_annealing": simulated_annealing_solver.solve,
    "parallel_tempering": parallel_tempering_solver.solve,
    "quantum_inspired": quantum_inspired_solver.solve,
}


def run_scenario(config: dict, solver_name: str, steps: int | None = None) -> tuple[list[dict], dict]:
    rng = seed_everything(int(config["scenario"].get("seed", 7)))
    topology = build_topology(config, rng)
    trace_replay = None
    if config["traffic"].get("trace_path"):
        trace_replay = TraceReplayDataset(config["traffic"]["trace_path"])
    users = create_users(config, rng, list(topology.base_stations), trace_replay=trace_replay)
    tracker = initialize_state(topology)
    scenario_name = config["scenario"]["name"]
    run_steps = int(steps or config["scenario"].get("steps", 6))
    rows = []
    exact_cutoff = int(config["solver"].get("exact_baseline_user_cutoff", 8))
    solver_fn = SOLVER_REGISTRY[solver_name]
    warm_start_ids: list[str] | None = None

    for time_slot in range(run_steps):
        paths_by_pair = pre_step_update(config, topology, users, tracker, rng, time_slot, trace_replay=trace_replay)
        instance = build_optimization_instance(config, scenario_name, time_slot, users, topology, paths_by_pair, tracker.edge_queues)
        exact_result = None
        if solver_name != "exact" and len(users) <= exact_cutoff:
            exact_result = ilp_solver.solve(instance)
        if config["solver"].get("warm_start", False) and warm_start_ids is not None:
            result = solver_fn(instance, initial_option_ids=warm_start_ids)
        else:
            result = solver_fn(instance)
        if exact_result is not None and abs(exact_result.objective_value) > 1e-9:
            result.quality_gap = (result.objective_value - exact_result.objective_value) / abs(exact_result.objective_value)
        warm_start_ids = [decision.option_id for decision in result.decisions]
        metrics = apply_decisions(
            config=config,
            topology=topology,
            tracker=tracker,
            instance=instance,
            decisions=result.decisions,
            paths_by_pair=paths_by_pair,
            solver_name=result.solver_name,
            objective_value=result.objective_value,
            solver_runtime_s=result.runtime_s,
            quality_gap=result.quality_gap,
            violations=result.violations,
        )
        rows.append(asdict(metrics))
    summary = aggregate_metrics([tracker_row["metrics"] for tracker_row in tracker.history])
    return rows, summary
