from __future__ import annotations

import copy

import pytest

from src.benchmarks.benchmark_config import load_scenario_config
from src.network.topology import build_topology
from src.optimization.decision_variables import build_optimization_instance
from src.simulation.event_loop import pre_step_update
from src.simulation.state_tracker import initialize_state
from src.utils.seed import seed_everything
from src.workloads.traffic_generator import create_users


def _base_config() -> dict:
    config = load_scenario_config("configs/base.yaml", "configs/simulation/wireless_dense.yaml")
    config["traffic"]["num_users"] = 5
    config["scenario"]["steps"] = 2
    config["solver"]["exact_baseline_user_cutoff"] = 6
    return config


@pytest.fixture
def config() -> dict:
    return copy.deepcopy(_base_config())


@pytest.fixture
def optimization_instance(config):
    rng = seed_everything(config["scenario"]["seed"])
    topology = build_topology(config, rng)
    users = create_users(config, rng, list(topology.base_stations))
    tracker = initialize_state(topology)
    paths = pre_step_update(config, topology, users, tracker, rng, time_slot=0)
    instance = build_optimization_instance(config, config["scenario"]["name"], 0, users, topology, paths, tracker.edge_queues)
    return config, topology, users, tracker, paths, instance

