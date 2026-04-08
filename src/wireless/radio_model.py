from __future__ import annotations

from src.utils.models import BaseStation, UserState
from src.wireless.interference_model import interference_penalty


def estimate_radio_capacity_mbps(
    user: UserState,
    station: BaseStation,
    active_users: int,
    num_base_stations: int,
    aggressiveness: float,
) -> float:
    penalty = interference_penalty(active_users, num_base_stations, aggressiveness)
    effective_efficiency = max(0.3, user.spectral_efficiency * penalty)
    return effective_efficiency * station.spectrum_mhz


def required_radio_units(throughput_mbps: float, spectral_efficiency: float, radio_unit_mhz: int) -> int:
    required_mhz = throughput_mbps / max(spectral_efficiency, 0.2)
    return max(1, int(round(required_mhz / max(1, radio_unit_mhz))))

