from __future__ import annotations

from src.utils.models import EdgeServer


def compute_service_time_ms(server: EdgeServer, compute_units: int) -> float:
    return 25.0 * compute_units / max(server.service_rate_units, 1)
