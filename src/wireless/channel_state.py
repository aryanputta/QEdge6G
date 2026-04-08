from __future__ import annotations

import numpy as np


def evolve_channel_quality(
    current_quality: float,
    rng: np.random.Generator,
    volatility: float,
    degradation: float = 0.0,
) -> float:
    drift = rng.normal(loc=-degradation, scale=volatility)
    return float(np.clip(current_quality + drift, 0.05, 1.0))

