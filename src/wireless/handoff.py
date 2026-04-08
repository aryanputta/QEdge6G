from __future__ import annotations

from src.network.mobility import attach_to_nearest_bs
from src.utils.models import BaseStation, UserState


def maybe_handoff(
    user: UserState,
    base_stations: dict[str, BaseStation],
    time_slot: int,
    hysteresis_km: float = 0.05,
    dwell_slots: int = 2,
    blackout_penalty_ms: float = 4.0,
) -> tuple[str, bool]:
    current = base_stations[user.attached_bs]
    current_distance = ((user.x - current.x) ** 2 + (user.y - current.y) ** 2) ** 0.5
    candidate = attach_to_nearest_bs(user, base_stations)
    best = base_stations[candidate]
    best_distance = ((user.x - best.x) ** 2 + (user.y - best.y) ** 2) ** 0.5
    if time_slot - user.last_handoff_slot < dwell_slots:
        user.attached_bs = current.bs_id
    elif current_distance <= best_distance + hysteresis_km:
        user.attached_bs = current.bs_id
    did_handoff = user.attached_bs != current.bs_id
    if did_handoff:
        user.last_handoff_slot = time_slot
        user.handoff_count += 1
        user.handoff_penalty_ms = blackout_penalty_ms
    else:
        user.handoff_penalty_ms *= 0.5
    return user.attached_bs, did_handoff
