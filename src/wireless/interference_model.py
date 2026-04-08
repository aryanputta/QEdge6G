from __future__ import annotations


def interference_penalty(active_users: int, num_base_stations: int, aggressiveness: float) -> float:
    density = active_users / max(1, num_base_stations)
    return max(0.5, 1.0 - aggressiveness * min(1.0, density / 12.0))

