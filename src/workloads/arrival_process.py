from __future__ import annotations

import numpy as np


def bursty_arrival(base_rate: float, burstiness: float, rng: np.random.Generator) -> float:
    burst_multiplier = rng.lognormal(mean=0.0, sigma=burstiness)
    if rng.random() < burstiness * 0.4:
        burst_multiplier *= 1.5 + burstiness
    return max(0.1, base_rate * burst_multiplier)

