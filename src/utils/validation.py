from __future__ import annotations


def validate_config(config: dict) -> None:
    required_sections = ["scenario", "topology", "traffic", "wireless", "edge", "solver"]
    missing = [section for section in required_sections if section not in config]
    if missing:
        raise ValueError(f"Missing required config sections: {missing}")
    if config["traffic"].get("num_users", 0) <= 0:
        raise ValueError("traffic.num_users must be positive")
    if config["topology"].get("num_base_stations", 0) <= 0:
        raise ValueError("topology.num_base_stations must be positive")
    if config["topology"].get("num_edges", 0) <= 0:
        raise ValueError("topology.num_edges must be positive")
    if config["solver"].get("bandwidth_unit_mbps", 0) <= 0:
        raise ValueError("solver.bandwidth_unit_mbps must be positive")
