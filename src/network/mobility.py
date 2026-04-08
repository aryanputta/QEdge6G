from __future__ import annotations

import math

import numpy as np

from src.utils.models import BaseStation, UserState


def update_user_position(user: UserState, rng: np.random.Generator, area_km: float) -> None:
    angle = float(rng.uniform(0.0, 2.0 * math.pi))
    distance = user.mobility_speed / 1000.0
    user.x = float(np.clip(user.x + math.cos(angle) * distance, 0.0, area_km))
    user.y = float(np.clip(user.y + math.sin(angle) * distance, 0.0, area_km))


def attach_to_nearest_bs(user: UserState, base_stations: dict[str, BaseStation]) -> str:
    best_bs = user.attached_bs
    best_distance = float("inf")
    for station in base_stations.values():
        distance = math.dist((user.x, user.y), (station.x, station.y))
        if distance < best_distance:
            best_distance = distance
            best_bs = station.bs_id
    user.attached_bs = best_bs
    return best_bs

